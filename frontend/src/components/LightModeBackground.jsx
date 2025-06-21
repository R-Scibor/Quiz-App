import React from 'react';

const LightModeBackground = () => (
  <div
    style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      zIndex: -1,
      backgroundColor: '#f3f4f6', // Jasnoszare tło (gray-100)
      backgroundImage: `
        repeating-linear-gradient(
          -45deg,
          transparent,
          transparent 15px,
          rgba(0, 0, 0, 0.04) 15px,
          rgba(0, 0, 0, 0.04) 16px
        )
      `,
    }}
  />
);

export default LightModeBackground;
