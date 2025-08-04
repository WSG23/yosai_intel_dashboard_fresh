import React from 'react';

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
  ...imgProps
}) => (
  <picture>
    {sources.map((source, index) => (
      <source key={index} {...source} />
    ))}
    <img {...imgProps} />
  </picture>
);

export default ResponsiveImage;
