import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import styled from 'styled-components';
import { useAuth } from '../contexts/AuthContext';

const LoginContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 200px);
  padding: 24px;
`;

const LoginCard = styled.div`
  background: white;
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
  border: 1px solid #eee;
`;

const Title = styled.h2`
  text-align: center;
  color: var(--primary-blue);
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 8px;
`;

const Subtitle = styled.p`
  text-align: center;
  color: #666;
  margin-bottom: 32px;
  font-size: 16px;
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 20px;
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 6px;
`;

const Label = styled.label`
  font-weight: 600;
  color: #333;
  font-size: 14px;
`;

const Input = styled.input`
  padding: 12px 16px;
  border: 2px solid #eee;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 0.2s ease;

  &:focus {
    outline: none;
    border-color: var(--primary-blue);
  }

  &::placeholder {
    color: #999;
  }
`;

const LoginButton = styled.button`
  background: linear-gradient(90deg, var(--primary-blue) 0%, var(--primary-magenta) 100%);
  color: white;
  border: none;
  padding: 14px 20px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s ease;
  margin-top: 8px;

  &:hover {
    opacity: 0.9;
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const ErrorMessage = styled.div`
  background: #ffe6e6;
  color: #c62828;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  border: 1px solid #ffcdd2;
`;

const SuccessMessage = styled.div`
  background: #e8f5e8;
  color: #2e7d32;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  border: 1px solid #c8e6c9;
`;

const AuthSwitch = styled.div`
  text-align: center;
  margin-top: 24px;
  color: #666;
  font-size: 14px;
`;

const SwitchLink = styled.button`
  color: var(--primary-blue);
  background: none;
  border: none;
  cursor: pointer;
  text-decoration: underline;
  font-size: 14px;

  &:hover {
    opacity: 0.8;
  }
`;

// PUBLIC_INTERFACE
const LoginPage = () => {
  const { login, register, isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (isAuthenticated && !loading) {
      navigate('/');
    }
  }, [isAuthenticated, loading, navigate]);

  const handleInputChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
    setError('');
    setSuccess('');
  };

  const validateForm = () => {
    if (!formData.username.trim()) {
      return 'Username is required';
    }

    if (!isLoginMode && !formData.email.trim()) {
      return 'Email is required';
    }

    if (!isLoginMode && !formData.email.includes('@')) {
      return 'Please enter a valid email address';
    }

    if (!formData.password) {
      return 'Password is required';
    }

    if (!isLoginMode && formData.password.length < 8) {
      return 'Password must be at least 8 characters long';
    }

    if (!isLoginMode && formData.password !== formData.confirmPassword) {
      return 'Passwords do not match';
    }

    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setSubmitting(true);
    setError('');
    setSuccess('');

    try {
      if (isLoginMode) {
        const result = await login({
          username: formData.username,
          password: formData.password
        });

        if (!result.success) {
          setError(result.error);
        }
      } else {
        const result = await register({
          username: formData.username,
          email: formData.email,
          password: formData.password
        });

        if (result.success) {
          setSuccess('Account created successfully! Please login.');
          setIsLoginMode(true);
          setFormData(prev => ({
            ...prev,
            password: '',
            confirmPassword: ''
          }));
        } else {
          setError(result.error);
        }
      }
    } catch (error) {
      setError('An unexpected error occurred. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const switchMode = () => {
    setIsLoginMode(!isLoginMode);
    setError('');
    setSuccess('');
    setFormData({
      username: formData.username,
      email: '',
      password: '',
      confirmPassword: ''
    });
  };

  if (loading) {
    return (
      <LoginContainer>
        <div>Loading...</div>
      </LoginContainer>
    );
  }

  return (
    <LoginContainer>
      <LoginCard>
        <Title>{isLoginMode ? 'Welcome Back' : 'Create Account'}</Title>
        <Subtitle>
          {isLoginMode ? 
            'Sign in to continue to your AI assistant' : 
            'Join to start chatting with documents'
          }
        </Subtitle>

        {error && <ErrorMessage>{error}</ErrorMessage>}
        {success && <SuccessMessage>{success}</SuccessMessage>}

        <Form onSubmit={handleSubmit}>
          <FormGroup>
            <Label htmlFor="username">Username</Label>
            <Input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleInputChange}
              placeholder="Enter your username"
              required
            />
          </FormGroup>

          {!isLoginMode && (
            <FormGroup>
              <Label htmlFor="email">Email</Label>
              <Input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="Enter your email"
                required
              />
            </FormGroup>
          )}

          <FormGroup>
            <Label htmlFor="password">Password</Label>
            <Input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              placeholder={isLoginMode ? "Enter your password" : "Create a password (min 8 characters)"}
              required
            />
          </FormGroup>

          {!isLoginMode && (
            <FormGroup>
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <Input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleInputChange}
                placeholder="Confirm your password"
                required
              />
            </FormGroup>
          )}

          <LoginButton type="submit" disabled={submitting}>
            {submitting ? 
              (isLoginMode ? 'Signing In...' : 'Creating Account...') :
              (isLoginMode ? 'Sign In' : 'Create Account')
            }
          </LoginButton>
        </Form>

        <AuthSwitch>
          {isLoginMode ? "Don't have an account? " : "Already have an account? "}
          <SwitchLink type="button" onClick={switchMode}>
            {isLoginMode ? 'Create one' : 'Sign in'}
          </SwitchLink>
        </AuthSwitch>
      </LoginCard>
    </LoginContainer>
  );
};

export default LoginPage;
