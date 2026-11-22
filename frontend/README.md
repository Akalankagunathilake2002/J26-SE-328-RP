This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

## Interview recordings to Google Drive

Candidates can opt in at interview setup to record the whole interview (Elena and their camera side by side,
both voices, Elena's words as captions). It is recorded in the browser (`src/lib/interviewRecorder.ts`) and
uploaded from the browser to the candidate's own Drive, folder "Skillaro Interviews"
(`src/lib/googleDrive.ts`); it never reaches Skillaro's servers. Without Google set up it can be downloaded.

Google Cloud setup (once, with any Google account):

1. console.cloud.google.com → new project → *APIs & Services → Library* → enable **Google Drive API**.
2. *OAuth consent screen*: External, app name "Skillaro", support e-mail, scope
   `https://www.googleapis.com/auth/drive.file`. While the app is in *Testing*, only the Google accounts added
   as test users (up to 100) can connect; *Publish app* opens it to everyone (`drive.file` is a non-sensitive
   scope, so no security review is required).
3. *Credentials → Create credentials → OAuth client ID → Web application*. Authorised JavaScript origins:
   `https://skillaro.dilmithranasinghe.com` and `http://localhost:3000`. No redirect URI is needed.
4. Set `NEXT_PUBLIC_GOOGLE_CLIENT_ID` to the client ID (Vercel project settings and `.env.local`), then
   redeploy: `NEXT_PUBLIC_` values are built into the page.

Size: about 4.5 MB a minute (a 25-minute interview is about 110 MB). Chrome and Edge record MP4, Firefox WebM.
The browser's built-in voice (used when the avatar is off) can't be recorded; captions cover it.
