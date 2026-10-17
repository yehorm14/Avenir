export function Icon({
  name,
  size = 20,
  ...rest
}: {
  name: string;
  size?: number;
  className?: string;
}) {
  const paths: Record<string, React.ReactNode> = {
    arrow: (
      <>
        <path d="M5 12h14M13 6l6 6-6 6" />
      </>
    ),
    back: <path d="m14 6-6 6 6 6" />,
    chevron: <path d="m9 5 7 7-7 7" />,
    check: <path d="m5 12 4 4L19 6" />,
    close: <path d="m6 6 12 12M6 18 18 6" />,
    plus: <path d="M12 5v14M5 12h14" />,
    compass: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="m16 8-3 5-5 3 3-5Z" />
      </>
    ),
    home: (
      <>
        <path d="m3 10 9-7 9 7M5 9v12h14V9M9 21v-7h6v7" />
      </>
    ),
    path: (
      <>
        <circle cx="5" cy="5" r="2" />
        <circle cx="19" cy="19" r="2" />
        <path d="M7 5h8a4 4 0 0 1 0 8H9a4 4 0 0 0 0 8h8" />
      </>
    ),
    calendar: (
      <>
        <rect x="4" y="5" width="16" height="16" rx="3" />
        <path d="M8 3v4m8-4v4M4 11h16m-11 4h2m3 0h2" />
      </>
    ),
    chat: (
      <>
        <path d="M21 11a8 8 0 0 1-8 8H6l-4 3V11a9 9 0 0 1 19 0Z" />
        <path d="M7 10h10M7 14h6" />
      </>
    ),
    chart: (
      <>
        <path d="M3 3v18h18M7 15l4-5 4 2 6-7" />
      </>
    ),
    pin: (
      <>
        <path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 0 1 14 0Z" />
        <circle cx="12" cy="10" r="2" />
      </>
    ),
    book: (
      <>
        <path d="M12 5c-4-2-8-1-9 0v15c3-2 6-2 9 0 3-2 6-2 9 0V5c-3-2-6-2-9 0Zm0 0v15" />
      </>
    ),
    code: (
      <>
        <path d="m8 6-6 6 6 6m8-12 6 6-6 6m-3-16-2 20" />
      </>
    ),
    building: (
      <>
        <path d="M4 21V8l8-5 8 5v13M2 21h20M8 10v2m8-2v2m-8 3v2m8-2v2m-5 4v-4h2v4" />
      </>
    ),
    bolt: <path d="m13 2-9 12h7l-1 8 10-13h-8Z" />,
    heart: (
      <path d="M20 5c-3-3-6-1-8 1-2-2-5-4-8-1-4 4 1 9 8 15 7-6 12-11 8-15Z" />
    ),
    design: (
      <>
        <path d="m4 17 13-13 3 3L7 20l-4 1Z" />
        <path d="m14 7 3 3" />
      </>
    ),
    shield: (
      <>
        <path d="m12 2 8 4v6c0 5-8 10-8 10S4 17 4 12V6Z" />
        <path d="m8 12 3 3 5-6" />
      </>
    ),
    money: (
      <>
        <rect x="2" y="5" width="20" height="14" rx="3" />
        <circle cx="12" cy="12" r="3" />
        <path d="M5 12h1m12 0h1" />
      </>
    ),
    search: (
      <>
        <circle cx="10" cy="10" r="6" />
        <path d="m15 15 6 6" />
      </>
    ),
    external: (
      <>
        <path d="M14 3h7v7m0-7L10 14M10 4H4v16h16v-6" />
      </>
    ),
    refresh: (
      <>
        <path d="M20 8a8 8 0 1 0 0 8M20 3v6h-6" />
      </>
    ),
    save: <path d="M6 3h12v19l-6-4-6 4Z" />,
    info: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 11v6m0-10v1" />
      </>
    ),
    download: (
      <>
        <path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5" />
      </>
    ),
    menu: <path d="M4 6h16M4 12h16M4 18h16" />,
    up: <path d="m6 14 6-6 6 6" />,
    down: <path d="m6 10 6 6 6-6" />,
    clock: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 6v6l4 2" />
      </>
    ),
    leaf: (
      <>
        <path d="M20 3C9 1 1 8 5 16c8 5 17-2 15-13ZM4 21 16 9" />
      </>
    ),
    lock: (
      <>
        <rect x="5" y="10" width="14" height="11" rx="3" />
        <path d="M8 10V7a4 4 0 0 1 8 0v3" />
      </>
    ),
  };
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.65"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...rest}
    >
      {paths[name] ?? paths.compass}
    </svg>
  );
}
export function careerIcon(soc: string) {
  return (
    (
      {
        "2134": "code",
        "3544": "chart",
        "2133": "code",
        "2135": "shield",
        "2141": "design",
        "2142": "design",
        "2451": "building",
        "2452": "building",
        "3120": "design",
        "2121": "building",
        "2123": "bolt",
        "3113": "bolt",
        "2453": "building",
        "2454": "compass",
        "2433": "chart",
        "2422": "money",
        "2421": "money",
        "2254": "heart",
        "5241": "bolt",
        "2313": "book",
      } as Record<string, string>
    )[soc] || "compass"
  );
}
