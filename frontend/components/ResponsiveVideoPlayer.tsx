import React, { useState, useRef, useEffect } from 'react';

interface ResponsiveVideoPlayerProps {
  url: string;
  className?: string;
}

const ResponsiveVideoPlayer: React.FC<ResponsiveVideoPlayerProps> = ({ url, className = '' }) => {
  const [videoAspectRatio, setVideoAspectRatio] = useState<'vertical' | 'horizontal' | 'square'>('horizontal');
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleLoadedMetadata = () => {
      const width = video.videoWidth;
      const height = video.videoHeight;
      
      if (width && height) {
        const aspectRatio = width / height;
        
        if (aspectRatio < 0.8) {
          setVideoAspectRatio('vertical');
        } else if (aspectRatio > 1.2) {
          setVideoAspectRatio('horizontal');
        } else {
          setVideoAspectRatio('square');
        }
      }
    };

    video.addEventListener('loadedmetadata', handleLoadedMetadata);
    video.load();

    return () => {
      video.removeEventListener('loadedmetadata', handleLoadedMetadata);
    };
  }, [url]);

  const convertGcsUrl = (videoUrl: string): string => {
    if (videoUrl.startsWith('gs://')) {
      const pathWithoutProtocol = videoUrl.substring(5);
      const bucketAndPath = pathWithoutProtocol.split('/');
      const bucketName = bucketAndPath[0];
      const pathOnly = bucketAndPath.slice(1).join('/');
      if (bucketName !== 'creative-audit-scratch-pad') {
        return `https://creative-audit.prd.cdn.polaris.prd.ext.wpromote.com/${pathOnly}`;
      }
      return `https://storage.googleapis.com/${pathWithoutProtocol}`;
    } else if (videoUrl.includes('storage.googleapis.com')) {
      const match = videoUrl.match(/storage\.googleapis\.com\/([^\/]+)\/(.+)/);
      if (match && match[1] && match[2]) {
        const bucketName = match[1];
        const pathOnly = match[2];
        if (bucketName !== 'creative-audit-scratch-pad') {
          return `https://creative-audit.prd.cdn.polaris.prd.ext.wpromote.com/${pathOnly}`;
        }
      }
    }
    return videoUrl;
  };

  const renderYouTubePlayer = (videoUrl: string) => {
    const videoId = videoUrl.split('v=')[1]?.split('&')[0];
    if (!videoId) return null;
    const embedUrl = `https://www.youtube.com/embed/${videoId}`;
    
    return (
      <iframe
        className={`w-full rounded-lg ${
          videoAspectRatio === 'vertical' 
            ? 'aspect-[9/16] max-w-sm mx-auto' 
            : 'aspect-video'
        } ${className}`}
        src={embedUrl}
        title="YouTube video player"
        frameBorder="0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
      />
    );
  };

  const renderVideoPlayer = () => {
    const videoUrl = convertGcsUrl(url);
    
    return (
      <video
        ref={videoRef}
        className={`w-full rounded-lg bg-black ${
          videoAspectRatio === 'vertical' 
            ? 'aspect-[9/16] max-w-sm mx-auto' 
            : videoAspectRatio === 'square'
            ? 'aspect-square max-w-md mx-auto'
            : 'aspect-video'
        } ${className}`}
        controls
      >
        <source src={videoUrl} type="video/mp4" />
        Your browser does not support the video tag.
      </video>
    );
  };

  if (url.includes('youtube.com/watch?v=')) {
    return renderYouTubePlayer(url);
  } else if (url.includes('storage.googleapis.com') || url.includes('creative-audit.prd.cdn.polaris.prd.ext.wpromote.com') || url.startsWith('gs://')) {
    return renderVideoPlayer();
  }

  return (
    <div className={`w-full aspect-video rounded-lg bg-gray-100 flex items-center justify-center ${className}`}>
      <p className="text-gray-500 text-sm">Video format not supported for preview.</p>
    </div>
  );
};

export default ResponsiveVideoPlayer;
