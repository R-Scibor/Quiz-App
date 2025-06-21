import React from 'react';

const DarkModeBackground = () => (
  <div
    style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      zIndex: -1,
      backgroundColor: '#1a1016', // Twój oryginalny kolor tła
      backgroundImage: `
        repeating-linear-gradient(
          -45deg,
          transparent,
          transparent 15px,
          rgba(255, 255, 255, 0.04) 15px,
          rgba(255, 255, 255, 0.04) 16px
        )
      `,
    }}
  />
);

export default DarkModeBackground;
