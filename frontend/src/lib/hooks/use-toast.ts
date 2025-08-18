// src/lib/hooks/use-toast.ts
import { toast } from 'sonner';

export const useToast = () => {
  return {
    toast: {
      success: (message: string, description?: string) => {
        toast.success(message, {
          description,
        });
      },
      error: (message: string, description?: string) => {
        toast.error(message, {
          description,
        });
      },
      info: (message: string, description?: string) => {
        toast.info(message, {
          description,
        });
      },
      warning: (message: string, description?: string) => {
        toast.warning(message, {
          description,
        });
      },
      loading: (message: string, description?: string) => {
        return toast.loading(message, {
          description,
        });
      },
      promise: <T,>(
        promise: Promise<T>,
        {
          loading,
          success,
          error,
        }: {
          loading: string;
          success: string | ((data: T) => string);
          error: string | ((error: any) => string);
        }
      ) => {
        return toast.promise(promise, {
          loading,
          success,
          error,
        });
      },
      dismiss: (toastId?: string | number) => {
        toast.dismiss(toastId);
      },
    },
  };
};