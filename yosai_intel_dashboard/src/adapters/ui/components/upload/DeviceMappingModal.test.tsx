import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DeviceMappingModal } from './DeviceMappingModal';

test('renders device modal title', () => {
  render(
    <DeviceMappingModal isOpen={true} onClose={() => {}} devices={['d1']} filename="file.csv" onConfirm={() => {}} />
  );
  expect(screen.getByText(/AI Device Classification/)).toBeInTheDocument();
});

test('tab cycles focus within the modal', async () => {
  jest.useFakeTimers();
  const user = userEvent.setup();
  render(
    <DeviceMappingModal
      isOpen={true}
      onClose={() => {}}
      devices={['d1']}
      filename="file.csv"
      onConfirm={() => {}}
    />
  );

  await act(async () => {
    jest.runAllTimers();
  });

  const confirm = screen.getByRole('button', { name: /confirm & train ai/i });
  const inputs = screen.getAllByRole('spinbutton');
  const firstInput = inputs[0];

  confirm.focus();
  expect(confirm).toHaveFocus();

  await user.tab();
  expect(firstInput).toHaveFocus();
});

test('shift+tab cycles focus backwards within the modal', async () => {
  jest.useFakeTimers();
  const user = userEvent.setup();
  render(
    <DeviceMappingModal
      isOpen={true}
      onClose={() => {}}
      devices={['d1']}
      filename="file.csv"
      onConfirm={() => {}}
    />
  );

  await act(async () => {
    jest.runAllTimers();
  });

  const confirm = screen.getByRole('button', { name: /confirm & train ai/i });
  const inputs = screen.getAllByRole('spinbutton');
  const firstInput = inputs[0];

  firstInput.focus();
  expect(firstInput).toHaveFocus();

  await user.tab({ shift: true });
  expect(confirm).toHaveFocus();
});
