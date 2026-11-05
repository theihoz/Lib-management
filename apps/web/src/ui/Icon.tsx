const paths: Record<string, string> = {
  book: "M4 4h6a3 3 0 0 1 3 3v14a4 4 0 0 0-4-3H4V4Zm18 0h-6a3 3 0 0 0-3 3v14a4 4 0 0 1 4-3h5V4Z",
  users:
    "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2m20 0v-2a4 4 0 0 0-3-3.87M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm8-7.87a4 4 0 0 1 0 7.75",
  user: "M20 21v-2a7 7 0 0 0-14 0v2M13 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z",
  scan: "M4 8V4h4m8 0h4v4m0 8v4h-4m-8 0H4v-4M7 9v6m4-6v6m3-6v6m3-6v6",
  return: "M9 4 4 9l5 5M4 9h10a6 6 0 0 1 0 12h-3",
  clock: "M12 7v5l3 2m7-2a10 10 0 1 1-20 0 10 10 0 0 1 20 0Z",
  wallet: "M3 6h17v15H3V6Zm0 0V3h14v3m-2 5h7v5h-7v-5Z",
  chart: "M4 3v18h18M8 16v-4m5 4V7m5 9v-6",
  archive: "M3 3h18v5H3V3Zm2 5v13h14V8m-10 5h6",
  settings:
    "M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Zm0-6v3m0 14v3M2 12h3m14 0h3M5 5l2 2m10 10 2 2M5 19l2-2M17 7l2-2",
  key: "M15 2a7 7 0 0 0-6 10L2 19v3h4v-3h3v-3l2-2a7 7 0 1 0 4-12Zm3 5h.01",
  search: "m21 21-5-5M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0Z",
  arrow: "M4 12h16m-6-6 6 6-6 6",
  chevron: "m9 5 7 7-7 7",
  menu: "M3 6h18M3 12h18M3 18h18",
  close: "m6 6 12 12M6 18 18 6",
  plus: "M12 4v16M4 12h16",
  check: "m5 12 4 4L19 6",
  alert: "M12 3 2 21h20L12 3Zm0 6v5m0 3v1",
  refresh: "M20 7v5h-5m5-1a8 8 0 1 0-1 7",
  logout: "M9 3H3v18h6m5-15 6 6-6 6m-7-6h13",
  print: "M6 9V3h12v6M6 18H3V9h18v9h-3M6 15h12v7H6v-7",
  download: "M12 3v12m-5-5 5 5 5-5M4 17v4h16v-4",
  bell: "M18 8a6 6 0 0 0-12 0v8l-2 2h16l-2-2V8Zm-8 13h4",
  home: "M3 11 12 3l9 8M5 9.5V21h5v-6h4v6h5V9.5",
  bookmark: "M6 3h12v18l-6-4-6 4V3Z",
  file: "M14 3H6v18h12V7l-4-4Zm0 0v4h4M9 12h6m-6 4h6",
  library: "M4 3v18m5-18v18M14 4l4 17M3 21h18",
  back: "M15 5 8 12l7 7",
  down: "m6 9 6 6 6-6",
  offline: "M2 8.8a15 15 0 0 1 20 0M5.5 12.4a10 10 0 0 1 13 0M9 16a5 5 0 0 1 6 0m-3 4h.01M3 3l18 18",
};
export function Icon({ name, size = 20 }: { name: string; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={paths[name] ?? paths.book} />
    </svg>
  );
}
