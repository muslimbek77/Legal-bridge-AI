import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { CloudArrowUpIcon, DocumentIcon, XMarkIcon } from '@heroicons/react/24/outline'
import clsx from 'clsx'

export default function FileUpload({ 
  files = [], 
  onFilesChange, 
  maxFiles = 1,
  accept = {
    'application/pdf': ['.pdf'],
    'application/msword': ['.doc'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'image/*': ['.png', '.jpg', '.jpeg', '.tiff'],
  },
  maxSize = 10 * 1024 * 1024, // 10MB
}) {
  const onDrop = useCallback((acceptedFiles) => {
    const newFiles = acceptedFiles.slice(0, maxFiles - files.length)
    onFilesChange([...files, ...newFiles])
  }, [files, maxFiles, onFilesChange])

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept,
    maxSize,
    maxFiles: maxFiles - files.length,
    disabled: files.length >= maxFiles,
  })

  const removeFile = (index) => {
    const newFiles = files.filter((_, i) => i !== index)
    onFilesChange(newFiles)
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="space-y-4">
      {files.length < maxFiles && (
        <div
          {...getRootProps()}
          className={clsx(
            'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
            isDragActive && !isDragReject && 'border-primary-500 bg-primary-50',
            isDragReject && 'border-red-500 bg-red-50',
            !isDragActive && 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
          )}
        >
          <input {...getInputProps()} />
          <CloudArrowUpIcon className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-2 text-sm text-gray-600">
            {isDragActive ? (
              isDragReject ? (
                <span className="text-red-600">Bu fayl turi qabul qilinmaydi</span>
              ) : (
                <span className="text-primary-600">Faylni shu yerga tashlang</span>
              )
            ) : (
              <>
                <span className="font-semibold text-primary-600">Fayl tanlash</span>
                {' yoki bu yerga tashlang'}
              </>
            )}
          </p>
          <p className="mt-1 text-xs text-gray-500">
            PDF, DOC, DOCX, PNG, JPG (maksimum {formatFileSize(maxSize)})
          </p>
        </div>
      )}

      {files.length > 0 && (
        <ul className="divide-y divide-gray-200 rounded-lg border border-gray-200">
          {files.map((file, index) => (
            <li key={index} className="flex items-center justify-between py-3 px-4">
              <div className="flex items-center min-w-0">
                <DocumentIcon className="h-8 w-8 text-gray-400 flex-shrink-0" />
                <div className="ml-3 min-w-0">
                  <a href={URL.createObjectURL(file)}  target ="_blank" rel="noopener noreferrer" className="text-sm font-medium text-gray-900 truncate">{file.name}</a>
                  <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => removeFile(index)}
                className="ml-4 flex-shrink-0 p-1 text-gray-400 hover:text-red-500"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
