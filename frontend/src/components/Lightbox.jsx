import React, { useCallback, useState } from 'react';
import { LightboxContext } from '../lightbox-context';

// Tiny app-wide lightbox so any evidence image can be zoomed with one click.
export function LightboxProvider({ children }) {
  const [src, setSrc] = useState(null);
  const open = useCallback((url) => setSrc(url), []);
  return (
    <LightboxContext.Provider value={open}>
      {children}
      {src && (
        <div className="lightbox" onClick={() => setSrc(null)}>
          <img src={src} alt="Evidence, enlarged" />
        </div>
      )}
    </LightboxContext.Provider>
  );
}
