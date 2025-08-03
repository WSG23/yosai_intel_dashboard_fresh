import { useEffect } from 'react';

type CommandMap = Record<string, () => void>;

export const useVoiceNavigation = (commands: CommandMap) => {
  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    const recognition = new SpeechRecognition();
    recognition.continuous = true;

    recognition.onresult = (event: any) => {
      const transcript = event.results[event.results.length - 1][0].transcript
        .trim()
        .toLowerCase();
      Object.entries(commands).forEach(([phrase, handler]) => {
        if (transcript.includes(phrase)) {
          handler();
        }
      });
    };

    recognition.start();
    return () => recognition.stop();
  }, [commands]);
};

export default useVoiceNavigation;
