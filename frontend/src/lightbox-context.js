import { createContext, useContext } from 'react';

// Split from Lightbox.jsx so that file only exports a component (keeps fast refresh happy).
export const LightboxContext = createContext(() => {});

export function useLightbox() {
  return useContext(LightboxContext);
}
