import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ChatInput from '../components/ChatInput';

describe('ChatInput Component', () => {
  it('renders input field', () => {
    render(<ChatInput onSendMessage={vi.fn()} isLoading={false} />);
    
    const input = screen.getByPlaceholderText(/message/i);
    expect(input).toBeInTheDocument();
  });

  it('calls onSendMessage when form is submitted', async () => {
    const handleSendMessage = vi.fn();
    const user = userEvent.setup();
    
    render(<ChatInput onSendMessage={handleSendMessage} isLoading={false} />);
    
    const input = screen.getByPlaceholderText(/message/i);
    await user.type(input, 'Test message');
    await user.keyboard('{Enter}');
    
    expect(handleSendMessage).toHaveBeenCalledWith('Test message');
  });

  it('clears input after sending message', async () => {
    const user = userEvent.setup();
    
    render(<ChatInput onSendMessage={vi.fn()} isLoading={false} />);
    
    const input = screen.getByPlaceholderText(/message/i) as HTMLInputElement;
    await user.type(input, 'Test message');
    await user.keyboard('{Enter}');
    
    expect(input.value).toBe('');
  });

  it('does not send empty messages', async () => {
    const handleSendMessage = vi.fn();
    const user = userEvent.setup();
    
    render(<ChatInput onSendMessage={handleSendMessage} isLoading={false} />);
    
    const input = screen.getByPlaceholderText(/message/i);
    await user.click(input);
    await user.keyboard('{Enter}');
    
    expect(handleSendMessage).not.toHaveBeenCalled();
  });

  it('does not send messages while loading', async () => {
    const handleSendMessage = vi.fn();
    const user = userEvent.setup();
    
    render(<ChatInput onSendMessage={handleSendMessage} isLoading={true} />);
    
    const input = screen.getByPlaceholderText(/message/i);
    await user.type(input, 'Test message');
    await user.keyboard('{Enter}');
    
    expect(handleSendMessage).not.toHaveBeenCalled();
  });

  it('disables send button while loading', () => {
    const { container } = render(<ChatInput onSendMessage={vi.fn()} isLoading={true} />);
    
    const button = container.querySelector('button[type="submit"]');
    expect(button).toBeDisabled();
  });

  it('enables send button when not loading and input has text', async () => {
    const user = userEvent.setup();
    const { container } = render(<ChatInput onSendMessage={vi.fn()} isLoading={false} />);
    
    const input = screen.getByPlaceholderText(/message/i);
    await user.type(input, 'Test');
    
    const button = container.querySelector('button[type="submit"]');
    expect(button).not.toBeDisabled();
  });
});
