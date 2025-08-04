import { Camera, CameraPhoto, CameraResultType } from '@capacitor/camera';

export interface CameraScan {
  /** Base64 encoded image string */
  image: string;
}

/** Capture a photo using the device camera and return it as base64. */
export const scan = async (): Promise<CameraScan> => {
  const photo: CameraPhoto = await Camera.getPhoto({
    resultType: CameraResultType.Base64,
  });

  return {
    image: photo.base64String ?? '',
  };
};

