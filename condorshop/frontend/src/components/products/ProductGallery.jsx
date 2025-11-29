import { useState } from 'react'

const ProductGallery = ({ images = [], productName = '' }) => {
  const [selectedIndex, setSelectedIndex] = useState(0)

  const displayImages = images.length > 0 ? images : [{ image: '/placeholder-product.jpg' }]

  return (
    <div className="space-y-4">
      {/* Main image */}
      <div className="aspect-square w-full overflow-hidden rounded-lg border border-gray-200 bg-gray-100">
        <img
          src={displayImages[selectedIndex]?.image || '/placeholder-product.jpg'}
          alt={productName}
          className="w-full h-full object-contain"
          loading="eager"
          width={600}
          height={600}
          onError={(e) => {
            e.target.src = '/placeholder-product.jpg'
          }}
        />
      </div>

      {/* Thumbnails */}
      {displayImages.length > 1 && (
        <div className="grid grid-cols-4 gap-2">
          {displayImages.map((img, index) => (
            <button
              key={index}
              onClick={() => setSelectedIndex(index)}
              className={`aspect-square overflow-hidden rounded-lg border-2 transition-all ${
                selectedIndex === index
                  ? 'border-primary-600 ring-2 ring-primary-200'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <img
                src={img.image}
                alt={`${productName} - Vista ${index + 1}`}
                className="w-full h-full object-cover"
                loading="lazy"
                width={150}
                height={150}
                onError={(e) => {
                  e.target.src = '/placeholder-product.jpg'
                }}
              />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default ProductGallery





