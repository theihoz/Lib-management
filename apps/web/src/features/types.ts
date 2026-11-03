export type ScreenDefinition = {
  id: string;
  group: string;
  kind: string;
  title: string;
  path: string;
  permission?: string;
  implemented: boolean;
  headers?: string[];
  fields?: string[];
  action?: string;
  note?: string;
  blocked?: boolean;
  conflict?: boolean;
  condition?: boolean;
  expired?: boolean;
  detail?: boolean;
};
