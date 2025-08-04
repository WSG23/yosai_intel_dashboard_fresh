import { BiometricAuth } from '@aparajita/capacitor-biometric-auth';

/** Check if biometric authentication is available on the device. */
export const isAvailable = async (): Promise<boolean> => {
  const { available } = await BiometricAuth.isAvailable();
  return available;
};

/** Prompt the user for biometric authentication. */
export const authenticate = async (): Promise<boolean> => {
  const { verified } = await BiometricAuth.verify();
  return verified;
};

