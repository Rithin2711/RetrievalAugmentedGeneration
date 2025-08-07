import React from "react";
import "./Header.css";

// Simple inline SVG for yellow/pink arrow
const ArrowIcon = () => (
  <svg width="32" height="32" viewBox="0 0 32 32">
    <defs>
      <linearGradient id="arrow-grad" x1="0" x2="1" y1="0.5" y2="0.5">
        <stop offset="0%" stopColor="#ffd900" />
        <stop offset="100%" stopColor="#aa188b" />
      </linearGradient>
    </defs>
    <polygon points="8,8 26,16 8,24" fill="url(#arrow-grad)" />
  </svg>
);

// PUBLIC_INTERFACE
// Header bar component for main layout

const Header = () => (
  <header className="backdrop-header">
    <div className="header-left">
      <span className="tataelxsi-logo">TATA&nbsp;ELXSI</span>
    </div>
    <div className="header-right">
      <span className="header-slogan">
        Home to a Billion <span className="possibilities-text">Possibilities</span>
      </span>
      <span className="header-arrow"><ArrowIcon /></span>
    </div>
  </header>
);

export default Header;
