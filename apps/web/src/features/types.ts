export type ScreenDefinition = {
  id: string; group: string; kind: string; title: string; path: string;
  permission?: string; implemented: boolean; headers?: string[]; fields?: string[];
  action?: string; note?: string; blocked?: boolean; conflict?: boolean;
  condition?: boolean; expired?: boolean; detail?: boolean;
};
export type Book = { id: string; title: string; author: string; year: string; available: number; color: string };
export type ScreenSample = {
  rows?: string[][]; values?: Record<string, string>; items?: string[][];
  books?: Book[]; receipt?: string;
};
export type ViewProps = {
  screen: ScreenDefinition; preview?: boolean; sample?: ScreenSample;
  navigate?: (screenId: string) => void;
};
