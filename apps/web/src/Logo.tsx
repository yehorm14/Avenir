/** The Aventier mark: a rising "A", a path that points forward. */
export function LogoMark({ size = 40 }: { size?: number }) {
  return (
    <svg
      className="logo-mark"
      width={size}
      height={size}
      viewBox="0 0 48 48"
      role="img"
      aria-label="Aventier"
    >
      <rect width="48" height="48" rx="13" fill="var(--foreground)" />
      <path
        d="M11 35 L24 11 L37 35"
        fill="none"
        stroke="var(--canvas)"
        strokeWidth="4.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M17 28 H31"
        stroke="var(--canvas)"
        strokeWidth="4.5"
        strokeLinecap="round"
      />
      <circle cx="24" cy="11" r="3.4" fill="#9fc1ff" />
    </svg>
  );
}
