import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ScaleIcon, EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import api from '@/services/api'

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    password_confirm: '',
    first_name: '',
    last_name: '',
    organization: '',
  })
  const [showPassword, setShowPassword] = useState(false)
  const [showPasswordConfirm, setShowPasswordConfirm] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate()

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!formData.email || !formData.password || !formData.first_name || !formData.last_name) {
      toast.error('Barcha majburiy maydonlarni to\'ldiring')
      return
    }
    
    if (formData.password !== formData.password_confirm) {
      toast.error('Parollar mos kelmaydi')
      return
    }
    
    if (formData.password.length < 8) {
      toast.error('Parol kamida 8 ta belgidan iborat bo\'lishi kerak')
      return
    }
    
    setIsLoading(true)
    
    try {
      await api.post('/api/v1/auth/register/', {
        email: formData.email,
        password: formData.password,
        password_confirm: formData.password_confirm,
        first_name: formData.first_name,
        last_name: formData.last_name,
        organization: formData.organization || undefined,
      })
      
      toast.success('Ro\'yxatdan muvaffaqiyatli o\'tdingiz! Endi tizimga kirishingiz mumkin.')
      navigate('/login')
    } catch (error) {
      const errorData = error.response?.data
      if (errorData?.email) {
        toast.error(errorData.email[0])
      } else if (errorData?.password) {
        toast.error(errorData.password[0])
      } else {
        toast.error('Ro\'yxatdan o\'tishda xatolik yuz berdi')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-blue-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="flex justify-center">
            <div className="flex items-center">
              <ScaleIcon className="h-12 w-12 text-primary-600" />
              <span className="ml-3 text-3xl font-bold text-gray-900">Legal Bridge AI</span>
            </div>
          </div>
          <h2 className="mt-6 text-center text-xl font-semibold text-gray-600">
            Ro'yxatdan o'tish
          </h2>
          <p className="mt-2 text-center text-sm text-gray-500">
            Yangi hisob yarating
          </p>
        </div>
        
        <div className="bg-white rounded-xl shadow-lg p-8">
          <form className="space-y-5" onSubmit={handleSubmit}>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="first_name" className="block text-sm font-medium text-gray-700">
                  Ism *
                </label>
                <input
                  id="first_name"
                  name="first_name"
                  type="text"
                  required
                  value={formData.first_name}
                  onChange={handleChange}
                  className="mt-1 input-field"
                  placeholder="Ismingiz"
                />
              </div>
              
              <div>
                <label htmlFor="last_name" className="block text-sm font-medium text-gray-700">
                  Familiya *
                </label>
                <input
                  id="last_name"
                  name="last_name"
                  type="text"
                  required
                  value={formData.last_name}
                  onChange={handleChange}
                  className="mt-1 input-field"
                  placeholder="Familiyangiz"
                />
              </div>
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email manzil *
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={formData.email}
                onChange={handleChange}
                className="mt-1 input-field"
                placeholder="sizning@email.uz"
              />
            </div>

            <div>
              <label htmlFor="organization" className="block text-sm font-medium text-gray-700">
                Tashkilot
              </label>
              <input
                id="organization"
                name="organization"
                type="text"
                value={formData.organization}
                onChange={handleChange}
                className="mt-1 input-field"
                placeholder="Tashkilot nomi (ixtiyoriy)"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Parol *
              </label>
              <div className="mt-1 relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={formData.password}
                  onChange={handleChange}
                  className="input-field pr-12"
                  placeholder="Kamida 8 ta belgi"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-primary-600 transition-colors duration-200"
                >
                  {showPassword ? (
                    <EyeSlashIcon className="h-5 w-5" aria-hidden="true" />
                  ) : (
                    <EyeIcon className="h-5 w-5" aria-hidden="true" />
                  )}
                </button>
              </div>
            </div>

            <div>
              <label htmlFor="password_confirm" className="block text-sm font-medium text-gray-700">
                Parolni tasdiqlang *
              </label>
              <div className="mt-1 relative">
                <input
                  id="password_confirm"
                  name="password_confirm"
                  type={showPasswordConfirm ? 'text' : 'password'}
                  required
                  value={formData.password_confirm}
                  onChange={handleChange}
                  className="input-field pr-12"
                  placeholder="Parolni qayta kiriting"
                />
                <button
                  type="button"
                  onClick={() => setShowPasswordConfirm(!showPasswordConfirm)}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-primary-600 transition-colors duration-200"
                >
                  {showPasswordConfirm ? (
                    <EyeSlashIcon className="h-5 w-5" aria-hidden="true" />
                  ) : (
                    <EyeIcon className="h-5 w-5" aria-hidden="true" />
                  )}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full btn-primary py-3 text-base"
            >
              {isLoading ? (
                <div className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Ro'yxatdan o'tilmoqda...
                </div>
              ) : (
                'Ro\'yxatdan o\'tish'
              )}
            </button>
          </form>
          
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Hisobingiz bormi?{' '}
              <Link to="/login" className="font-medium text-primary-600 hover:text-primary-500">
                Tizimga kiring
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
