import React from 'react';
import { usePreferencesStore } from '../state';
import { useNetworkStatus } from '../lib/network';

interface Source {
  srcSet: string;
  media: string;
  type?: string;
}

interface ResponsiveImageProps
  extends React.ImgHTMLAttributes<HTMLImageElement> {
  sources: Source[];
}

const ResponsiveImage: React.FC<ResponsiveImageProps> = ({
  sources,
  src,
  alt = '',
  ...imgProps
}) => {
  const { saveData } = usePreferencesStore();
  const network = useNetworkStatus();
  const slow =
    ['slow-2g', '2g'].includes(network.effectiveType ?? '') || network.saveData;
  const shouldReduce = saveData || slow;

  if (shouldReduce) {
    const lowSrc = src ?? sources[0]?.srcSet;
    return <img alt={alt} {...imgProps} src={lowSrc} />;
  }

  return (
    <picture>
      {sources.map((source, index) => (
        <source key={index} {...source} />
      ))}
      <img alt={alt} {...imgProps} src={src} />
    </picture>
  );
};

export default ResponsiveImage;
