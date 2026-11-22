# Model host: run the GPU models on a Mac for a hosted server

The services (gateway, auth, learning, interview, database) can run on a server without a GPU, while Gemma
and the avatar engine run on a Mac with Apple silicon. The Mac is usually behind NAT (a home router or a
phone hotspot), so it is published through an ngrok tunnel, and an access-key gateway sits in front of the
models because `mlx_lm.server` and the avatar engine have no authentication of their own.

```
browser ──► server (API_GATEWAY_URL) ──► learning / interview services ──HTTPS + key──► ngrok ──► Mac
                                                                                    model_gateway.py :8090
                                                                                      /llm    → Gemma :8082
                                                                                      /avatar → avatar :8768
```

## Start

```bash
scripts/model-host/start-model-host.sh                 # Gemma + gateway + tunnel
NO_AVATAR=1 scripts/model-host/start-model-host.sh     # without the avatar engine
```

It prints the values to set on the server for both services, then restart them:

| Setting | Value |
|---|---|
| `LLM_PROVIDER` | `local` |
| `LOCAL_LLM_URL` | `https://<tunnel>/llm` |
| `MODEL_HOST_KEY` | the key in `~/.skillbridge-local/model-host.key` (made on first start, never committed) |
| `AVATAR_PROVIDER` | `none`, or `local` with `LOCAL_AVATAR_URL=https://<tunnel>/avatar` |

The account's ngrok domain stays the same between restarts. Requests without the key get 401.
Check from anywhere: `curl -H "Authorization: Bearer $(cat ~/.skillbridge-local/model-host.key)" https://<tunnel>/health`.

## Measured (19 October 2026, MacBook with 16 GB)

| | Result |
|---|---|
| Gemma 4 E4B (4-bit MLX) memory | 4.8 GB footprint, 5.1 GB peak |
| Prompt cache (`--prompt-cache-size 8`) | repeated 1,284-token instructions: 4.3 s first call, 1.2–1.3 s after |
| Embedding one text per ONNX call instead of 32 (services) | peak 3.4 GB → 327 MB, corpus embedding 2.3x faster |
| ONNX memory arena off | worse: 4.4 GB peak, so it stays on |
| `ONNX_THREADS=2` | slower (46 s vs 38 s for 1,500 chunks); only for a crowded shared host |

## Limits

- Interviews and lessons only work while the Mac is awake and online.
- The avatar's videos travel Mac → server → browser, so they need a good upload; on a phone hotspot, use
  `AVATAR_PROVIDER=none` (the browser speaks the questions instead).
- ngrok's free plan limits bandwidth and requests per month; LLM traffic is small, avatar video is not.
