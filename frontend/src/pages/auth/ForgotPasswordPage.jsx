import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ScaleIcon, EnvelopeIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import api from '@/services/api' 

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmitted, setIsSubmitted] = useState(false)
  const [resetToken, setResetToken] = useState(null) // For demo only

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!email) {
      toast.error('Email manzilini kiriting')
      return
    }
    
    setIsLoading(true)
    
    try {
      const response = await api.post('/api/v1/auth/password-reset/', { 
        email,
        frontend_url: window.location.origin 
      })
      setIsSubmitted(true)
      
      // Agar email yuborishda xatolik bo'lsa, demo token ko'rsatiladi
      if (response.data.demo_token) {
        setResetToken(response.data.demo_token)
        toast.error('Email yuborib bo\'lmadi. Demo token ko\'rsatildi.')
      } else {
        toast.success('Ko\'rsatmalar emailingizga yuborildi')
      }
    } catch (error) {
      toast.error('Xatolik yuz berdi. Qayta urinib ko\'ring.')
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
            Parolni tiklash
          </h2>
          <p className="mt-2 text-center text-sm text-gray-500">
            Email manzilingizni kiriting, parolni tiklash uchun ko'rsatmalar yuboramiz
          </p>
        </div>
        
        <div className="bg-white rounded-xl shadow-lg p-8">
          {!isSubmitted ? (
            <form className="space-y-6" onSubmit={handleSubmit}>
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                  Email manzil
                </label>
                <div className="mt-1 relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <EnvelopeIcon className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="input-field pl-10"
                    placeholder="sizning@email.uz"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full btn-primary py-3 text-base"
              >
                {isLoading ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Yuborilmoqda...
                  </span>
                ) : (
                  'Parolni tiklash'
                )}
              </button>
            </form>
          ) : (
            <div className="text-center space-y-4">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
                <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900">Email yuborildi!</h3>
              <p className="text-sm text-gray-500">
                {email} manziliga parolni tiklash uchun ko'rsatmalar yuborildi.
                Iltimos, pochta qutingizni tekshiring.
              </p>
              
              {/* Demo uchun - productionda olib tashlang */}
              {resetToken && (
                <div className="mt-4 p-4 bg-yellow-50 rounded-lg">
                  <p className="text-xs text-yellow-800 font-medium">Demo rejim:</p>
                  <p className="text-xs text-yellow-700 mt-1">
                    Parolni tiklash uchun quyidagi linkka o'ting:
                  </p>
                  <Link 
                    to={`/reset-password?token=${resetToken}`}
                    className="text-xs text-primary-600 hover:text-primary-500 break-all"
                  >
                    /reset-password?token={resetToken}
                  </Link>
                </div>
              )}
            </div>
          )}
          
          <div className="mt-6 text-center">
            <Link to="/login" className="text-sm font-medium text-primary-600 hover:text-primary-500">
              ← Tizimga kirishga qaytish
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
