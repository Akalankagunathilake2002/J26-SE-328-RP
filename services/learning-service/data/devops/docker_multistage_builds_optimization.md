# Docker Multi-Stage Builds and Container Image Optimization

## The Bloated Container Anti-Pattern
A naive single-stage Dockerfile copies source code, downloads compilers and package managers (GCC, Node.js SDK, Maven, Python build-tools), and produces bloated production images exceeding 1.5 GB.
Large images create significant operational drawbacks:
- Slow pull and deploy times across CI/CD runners and Kubernetes cluster nodes.
- High memory usage and disk storage costs in container registries.
- **Expanded Attack Surface**: Inclusion of development compilers, shell interpreters, and build dependencies introduces hundreds of unnecessary Common Vulnerabilities and Exposures (CVEs).

## Architecture of Multi-Stage Builds
Multi-Stage builds allow developers to define multiple `FROM` instructions in a single `Dockerfile`. Each stage can use a different base image, selectively copying artifacts from previous stages into a minimal production base image.

```dockerfile
# Stage 1: Build & Compilation
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Minimal Production Runtime
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
# Copy only the compiled output and production node_modules from builder
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/public ./public
USER node
EXPOSE 3000
CMD ["node", "server.js"]
```

## Best Practices for Production Containerization
1. **Layer Caching Optimization**: Order Docker instructions from least-frequently changed to most-frequently changed. Copy dependency descriptors (`package.json`, `requirements.txt`, `go.mod`) and install dependencies *before* copying application source code.
2. **Minimal Base Images**: Use Alpine Linux (`alpine`), Google Distroless (`gcr.io/distroless/`), or Scratch images. Distroless images contain only the application runtime and its runtime dependencies, omitting package managers, shells (`/bin/sh`), and utilities.
3. **Non-Root Execution**: Always declare a non-privileged `USER` directive to mitigate container escape vulnerabilities.
4. **`.dockerignore` Rigor**: Exclude `.git`, `node_modules`, test files, `.env` secrets, and local logs from entering the Docker build context.
