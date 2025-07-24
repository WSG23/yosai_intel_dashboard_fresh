import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || '/api';

export const useCallbackApi = () => {
  const toggleCustomField = async (selected: string) => {
    const res = await axios.post(`${API_URL}/v1/callbacks/toggle-custom-field`, { selected_value: selected });
    return res.data;
  };

  return {
    toggleCustomField,
  };
};
