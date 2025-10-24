import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import ResponsiveVideoPlayer from '../components/ResponsiveVideoPlayer';

describe('ResponsiveVideoPlayer Component', () => {
  it('renders video player with GCS URL', () => {
    const videoUrl = 'https://storage.googleapis.com/bucket-name/video.mp4';
    
    const { container } = render(<ResponsiveVideoPlayer url={videoUrl} />);
    
    const video = container.querySelector('video');
    expect(video).toBeInTheDocument();
    expect(video?.querySelector('source')).toHaveAttribute('src');
  });

  it('renders with controls enabled', () => {
    const { container } = render(<ResponsiveVideoPlayer url="https://storage.googleapis.com/bucket/video.mp4" />);
    
    const video = container.querySelector('video');
    expect(video).toHaveAttribute('controls');
  });

  it('renders YouTube player for YouTube URLs', () => {
    const { container } = render(
      <ResponsiveVideoPlayer url="https://www.youtube.com/watch?v=test123" />
    );
    
    expect(container.querySelector('iframe')).toBeInTheDocument();
  });

  it('has proper styling classes for video', () => {
    const { container } = render(<ResponsiveVideoPlayer url="https://storage.googleapis.com/bucket/video.mp4" />);
    
    const video = container.querySelector('video');
    expect(video).toHaveClass('rounded-lg');
  });
  
  it('renders unsupported message for other URLs', () => {
    render(<ResponsiveVideoPlayer url="https://example.com/video.mp4" />);
    
    expect(screen.getByText(/not supported/i)).toBeInTheDocument();
  });
});
