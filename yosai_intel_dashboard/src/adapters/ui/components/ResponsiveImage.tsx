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
  ...imgProps
}) => {
  const { saveData } = usePreferencesStore();
  const network = useNetworkStatus();
  const slow =
    ['slow-2g', '2g'].includes(network.effectiveType ?? '') || network.saveData;
  const shouldReduce = saveData || slow;

  if (shouldReduce) {
    const lowSrc = src ?? sources[0]?.srcSet;
    return <img {...imgProps} src={lowSrc} />;
  }

  return (
    <picture>
      {sources.map((source, index) => (
        <source key={index} {...source} />
      ))}
      <img {...imgProps} src={src} />
    </picture>
  );
};

export default ResponsiveImage;
