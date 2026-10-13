import { useEffect } from "react";
import { create } from "zustand";

interface PageTitleState {
  title: string;
  ownHeader: boolean;
  setTitle: (title: string) => void;
  setOwnHeader: (value: boolean) => void;
}

export const usePageTitleStore = create<PageTitleState>((set) => ({
  title: "",
  ownHeader: false,
  setTitle: (title) => set({ title }),
  setOwnHeader: (ownHeader) => set({ ownHeader }),
}));

/** Cada página llama esto para anunciar su título al layout. */
export function usePageTitle(title: string): void {
  const setTitle = usePageTitleStore((state) => state.setTitle);
  useEffect(() => {
    setTitle(title);
  }, [title, setTitle]);
}

/** Marca que la página pinta su propio PageHeader, para que el layout no duplique el título. */
export function useOwnPageHeader(): void {
  const setOwnHeader = usePageTitleStore((state) => state.setOwnHeader);
  useEffect(() => {
    setOwnHeader(true);
    return () => setOwnHeader(false);
  }, [setOwnHeader]);
}
