import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Message from '../components/Message';
import { Role } from '../types';

describe('Message Component', () => {
  it('renders user message correctly', () => {
    const message = {
      role: Role.USER,
      text: 'Hello, AI!'
    };

    render(<Message message={message} />);
    
    expect(screen.getByText('Hello, AI!')).toBeInTheDocument();
  });

  it('renders bot message correctly', () => {
    const message = {
      role: Role.MODEL,
      text: 'Hello, human!'
    };

    render(<Message message={message} />);
    
    expect(screen.getByText('Hello, human!')).toBeInTheDocument();
  });

  it('formats bold text correctly', () => {
    const message = {
      role: Role.MODEL,
      text: 'This is **bold** text'
    };

    const { container } = render(<Message message={message} />);
    
    const strong = container.querySelector('strong');
    expect(strong).toBeInTheDocument();
    expect(strong?.textContent).toBe('bold');
  });

  it('formats inline code correctly', () => {
    const message = {
      role: Role.MODEL,
      text: 'Use `console.log()` to debug'
    };

    const { container } = render(<Message message={message} />);
    
    const code = container.querySelector('code');
    expect(code).toBeInTheDocument();
    expect(code?.textContent).toBe('console.log()');
  });

  it('does not render empty bot messages', () => {
    const message = {
      role: Role.MODEL,
      text: ''
    };

    const { container } = render(<Message message={message} />);
    
    expect(container.firstChild).toBeNull();
  });

  it('renders video media attachment', () => {
    const message = {
      role: Role.MODEL,
      text: 'Here is your edited video',
      media: {
        video_url: 'https://example.com/video.mp4'
      }
    };

    render(<Message message={message} />);
    
    expect(screen.getByText('Here is your edited video')).toBeInTheDocument();
    expect(screen.getByText('Edited Video')).toBeInTheDocument();
  });

  it('renders audio media attachments', () => {
    const message = {
      role: Role.MODEL,
      text: 'Here is your audio',
      media: {
        audio_urls: ['https://example.com/audio1.mp3', 'https://example.com/audio2.mp3']
      }
    };

    render(<Message message={message} />);
    
    expect(screen.getByText('Here is your audio')).toBeInTheDocument();
    expect(screen.getByText('Generated Audio (2)')).toBeInTheDocument();
    expect(screen.getByText('Audio 1')).toBeInTheDocument();
    expect(screen.getByText('Audio 2')).toBeInTheDocument();
  });

  it('applies correct styling for user messages', () => {
    const message = {
      role: Role.USER,
      text: 'User message'
    };

    const { container } = render(<Message message={message} />);
    
    const bubble = container.querySelector('.bg-\\[\\#1a2b52\\]');
    expect(bubble).toBeInTheDocument();
  });

  it('applies correct styling for bot messages', () => {
    const message = {
      role: Role.MODEL,
      text: 'Bot message'
    };

    const { container } = render(<Message message={message} />);
    
    const bubble = container.querySelector('.bg-white');
    expect(bubble).toBeInTheDocument();
  });
});
