import { render, screen } from '@testing-library/react';
import Welcome from './Welcome';

test('renders welcome heading', () => {
  render(<Welcome />);
  expect(screen.getByText(/What would you like to learn today/)).toBeInTheDocument();
});
