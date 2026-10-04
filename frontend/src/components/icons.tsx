import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

/** Base for 24×24 line icons. */
function LineIcon({ children, ...props }: IconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      {children}
    </svg>
  );
}

/** Base for 24×24 filled brand icons. */
function FilledIcon({ children, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...props}>
      {children}
    </svg>
  );
}

export const UsersIcon = (props: IconProps) => (
  <LineIcon {...props}>
    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
    <circle cx="9" cy="7" r="4" />
    <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
    <path d="M16 3.13a4 4 0 0 1 0 7.75" />
  </LineIcon>
);

export const BriefcaseIcon = (props: IconProps) => (
  <LineIcon {...props}>
    <rect width="20" height="14" x="2" y="7" rx="2" />
    <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
  </LineIcon>
);

export const ChartIcon = (props: IconProps) => (
  <LineIcon {...props}>
    <path d="M3 3v16a2 2 0 0 0 2 2h16" />
    <path d="M7 16h8" />
    <path d="M7 11h12" />
    <path d="M7 6h3" />
  </LineIcon>
);

export const CheckIcon = (props: IconProps) => (
  <LineIcon {...props}>
    <path d="M20 6 9 17l-5-5" />
  </LineIcon>
);

export const StarIcon = (props: IconProps) => (
  <LineIcon {...props}>
    <path d="m12 2 3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z" />
  </LineIcon>
);

export const TrendingUpIcon = (props: IconProps) => (
  <LineIcon {...props}>
    <path d="m22 7-8.5 8.5-5-5L2 17" />
    <path d="M16 7h6v6" />
  </LineIcon>
);

export const UserIcon = (props: IconProps) => (
  <LineIcon {...props}>
    <circle cx="12" cy="8" r="4" />
    <path d="M20 21a8 8 0 0 0-16 0" />
  </LineIcon>
);

export const TargetIcon = (props: IconProps) => (
  <LineIcon {...props}>
    <circle cx="12" cy="12" r="10" />
    <circle cx="12" cy="12" r="6" />
    <circle cx="12" cy="12" r="2" />
  </LineIcon>
);

export const BookIcon = (props: IconProps) => (
  <LineIcon {...props}>
    <rect width="14" height="18" x="5" y="3" rx="2" />
    <path d="M5 17h14" />
  </LineIcon>
);

export const MessageIcon = (props: IconProps) => (
  <LineIcon {...props}>
    <path d="M7.9 20A9 9 0 1 0 4 16.1L2 22z" />
  </LineIcon>
);

export const ArrowRightIcon = (props: IconProps) => (
  <LineIcon {...props}>
    <path d="M5 12h14" />
    <path d="m12 5 7 7-7 7" />
  </LineIcon>
);

export const ArrowUpRightIcon = (props: IconProps) => (
  <LineIcon {...props}>
    <path d="M7 7h10v10" />
    <path d="M7 17 17 7" />
  </LineIcon>
);

export const ChevronCircleIcon = (props: IconProps) => (
  <LineIcon {...props}>
    <circle cx="12" cy="12" r="10" />
    <path d="m10.5 8 4 4-4 4" />
  </LineIcon>
);

export const MailIcon = (props: IconProps) => (
  <FilledIcon {...props}>
    <path d="M3 5h18a1 1 0 0 1 1 1v.6l-10 6.2L2 6.6V6a1 1 0 0 1 1-1z" />
    <path d="M2 8.9l10 6.2 10-6.2V18a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1z" />
  </FilledIcon>
);

export const PhoneIcon = (props: IconProps) => (
  <FilledIcon {...props}>
    <path d="M6.6 10.8a15.2 15.2 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25 11.4 11.4 0 0 0 3.6.57 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.25.2 2.45.57 3.57a1 1 0 0 1-.25 1z" />
  </FilledIcon>
);

export const MapPinIcon = (props: IconProps) => (
  <FilledIcon {...props}>
    <path d="M12 2a8 8 0 0 0-8 8c0 5.4 7 11.5 7.3 11.8a1 1 0 0 0 1.4 0C13 21.5 20 15.4 20 10a8 8 0 0 0-8-8zm0 11a3 3 0 1 1 0-6 3 3 0 0 1 0 6z" />
  </FilledIcon>
);

export const FacebookIcon = (props: IconProps) => (
  <FilledIcon {...props}>
    <path d="M24 12.07C24 5.4 18.63 0 12 0S0 5.4 0 12.07C0 18.1 4.39 23.1 10.13 24v-8.44H7.08v-3.49h3.05V9.41c0-3.02 1.79-4.7 4.53-4.7 1.31 0 2.69.24 2.69.24v2.97h-1.52c-1.49 0-1.96.93-1.96 1.89v2.26h3.33l-.53 3.49h-2.8V24C19.61 23.1 24 18.1 24 12.07z" />
  </FilledIcon>
);

export const TwitterIcon = (props: IconProps) => (
  <FilledIcon {...props}>
    <path d="M23.95 4.57a10 10 0 0 1-2.82.78 4.96 4.96 0 0 0 2.16-2.73c-.95.56-2 .96-3.13 1.19a4.92 4.92 0 0 0-8.38 4.48A13.96 13.96 0 0 1 1.64 3.16a4.92 4.92 0 0 0 1.52 6.57 4.9 4.9 0 0 1-2.23-.62v.06a4.92 4.92 0 0 0 3.95 4.83 4.99 4.99 0 0 1-2.21.08 4.94 4.94 0 0 0 4.6 3.42A9.87 9.87 0 0 1 0 19.54a14 14 0 0 0 7.56 2.21c9.05 0 14-7.5 14-13.98 0-.21 0-.42-.02-.63A9.94 9.94 0 0 0 24 4.59z" />
  </FilledIcon>
);

export const LinkedInIcon = (props: IconProps) => (
  <FilledIcon {...props}>
    <path d="M20.45 20.45h-3.56v-5.57c0-1.33-.02-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28zM5.34 7.43a2.06 2.06 0 1 1 0-4.13 2.06 2.06 0 0 1 0 4.13zM7.12 20.45H3.56V9h3.56v11.45zM22.22 0H1.77C.79 0 0 .77 0 1.73v20.54C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.73V1.73C24 .77 23.2 0 22.22 0z" />
  </FilledIcon>
);

/** Hand-drawn loop doodle next to section tags. */
export const SquiggleDoodle = (props: IconProps) => (
  <svg viewBox="0 0 40 26" fill="none" stroke="currentColor" strokeWidth={2.4} strokeLinecap="round" aria-hidden="true" {...props}>
    <path d="M3 9c3-6 10-6 9-1-1 4-7 4-5 8 2 3 8-2 12-5 4-3 8-1 6 3-2 3-6 4-4 7 2 2 7-1 11-3" />
  </svg>
);

/** Four-point sparkle with a small plus and dot. */
export const SparkleDoodle = (props: IconProps) => (
  <svg viewBox="0 0 40 40" fill="none" stroke="currentColor" strokeWidth={2.4} strokeLinejoin="round" strokeLinecap="round" aria-hidden="true" {...props}>
    <path d="M17 10c1 7 3 9 10 10-7 1-9 3-10 10-1-7-3-9-10-10 7-1 9-3 10-10z" />
    <path d="M31 3v6M28 6h6" />
    <circle cx="6" cy="34" r="2" />
  </svg>
);
