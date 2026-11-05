import { createContext, useContext, useEffect } from "react";

/** Lets a detail screen replace the generic heading with the record it shows. */
export const PageTitleContext = createContext<(title: string | undefined) => void>(() => {});

export function usePageTitle(title: string | undefined) {
  const set = useContext(PageTitleContext);
  useEffect(() => {
    set(title);
    return () => set(undefined);
  }, [set, title]);
}

export const DEFAULT_LIBRARY_NAME = "Thư viện";
export const LibraryNameContext = createContext(DEFAULT_LIBRARY_NAME);

export function useLibraryName() {
  return useContext(LibraryNameContext);
}

export function useDocumentTitle(title: string) {
  const library = useLibraryName();
  useEffect(() => {
    document.title = title === library ? library : `${title} · ${library}`;
  }, [title, library]);
}
