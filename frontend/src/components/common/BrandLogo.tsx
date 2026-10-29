import React from 'react';
import { BRAND_CONFIG } from '../../assets/brand.config';

interface BrandLogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showText?: boolean;
  light?: boolean;
  className?: string;
}

export const BrandLogo: React.FC<BrandLogoProps> = ({
  size = 'md',
  showText = true,
  light = false,
  className = ''
}) => {
  const sizeMap = {
    sm: { img: 'w-8 h-8', title: 'text-sm', sub: 'text-[9px]' },
    md: { img: 'w-11 h-11', title: 'text-base', sub: 'text-[10px]' },
    lg: { img: 'w-16 h-16', title: 'text-xl', sub: 'text-xs' },
    xl: { img: 'w-24 h-24', title: 'text-2xl', sub: 'text-sm' },
  };

  const currentSize = sizeMap[size];

  return (
    <div className={`flex items-center gap-3 select-none ${className}`}>
      <div className={`relative ${currentSize.img} flex-shrink-0 transition-transform duration-300 hover:scale-105`}>
        {BRAND_CONFIG.customLogoImage ? (
          <img
            src={BRAND_CONFIG.customLogoImage}
            alt={BRAND_CONFIG.name}
            className="w-full h-full object-contain"
          />
        ) : (
          <img
            src="/logo.svg"
            alt={BRAND_CONFIG.name}
            className="w-full h-full object-contain drop-shadow-sm"
          />
        )}
      </div>

      {showText && (
        <div className="flex flex-col">
          <span
            className={`font-serif font-bold tracking-wider leading-none ${
              light ? 'text-white' : 'text-ssk-navy'
            } ${currentSize.title}`}
          >
            SREE SAI KRISHNA
          </span>
          <span
            className={`font-sans font-semibold tracking-widest uppercase leading-tight ${
              light ? 'text-ssk-gold-light' : 'text-ssk-gold'
            } ${currentSize.sub}`}
          >
            COLLECTIONS
          </span>
        </div>
      )}
    </div>
  );
};
