import { createContext, useContext, useEffect } from "react";

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
