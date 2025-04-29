import axios from './axiosInstance';

export const login = async (credentials) => {
  return axios.post('/auth/login', credentials);
};

export const signup = async (data) => {
  return axios.post('/auth/signup', data);
};
