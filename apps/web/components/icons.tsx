import { ReactNode } from "react";

type IconProps = { className?: string };

function base(path: ReactNode) {
  return function Icon({ className }: IconProps) {
    return (
      <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        {path}
      </svg>
    );
  };
}

export const ScopeIcon = base(
  <>
    <circle cx="11" cy="11" r="7" />
    <path d="m21 21-4.3-4.3" />
    <path d="M11 8v6M8 11h6" />
  </>
);

export const ShieldIcon = base(
  <>
    <path d="M12 3 5 6v5c0 4.4 3 7.4 7 9 4-1.6 7-4.6 7-9V6z" />
    <path d="m9.5 12 1.7 1.7 3.3-3.4" />
  </>
);

export const RulesIcon = base(
  <>
    <path d="M5 4h14v16H5z" />
    <path d="M8 8h8M8 12h8M8 16h5" />
  </>
);

export const LayersIcon = base(
  <>
    <path d="m12 3 9 5-9 5-9-5z" />
    <path d="m3 13 9 5 9-5" />
  </>
);

export const BookIcon = base(
  <>
    <path d="M5 4h10a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3z" />
    <path d="M5 17a3 3 0 0 1 3-3h10" />
  </>
);

export const SparkIcon = base(
  <>
    <path d="M12 3v4M12 17v4M3 12h4M17 12h4" />
    <path d="m6 6 2.5 2.5M15.5 15.5 18 18M18 6l-2.5 2.5M8.5 15.5 6 18" />
  </>
);

export const UploadIcon = base(
  <>
    <path d="M12 16V4" />
    <path d="m7 9 5-5 5 5" />
    <path d="M5 20h14" />
  </>
);

export const CopyIcon = base(
  <>
    <rect x="9" y="9" width="11" height="11" rx="2" />
    <path d="M5 15V5a2 2 0 0 1 2-2h8" />
  </>
);

export const CheckIcon = base(<path d="m5 12 5 5 9-10" />);

export const PlayIcon = base(<path d="M7 4v16l13-8z" />);
