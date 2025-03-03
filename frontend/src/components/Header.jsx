import { useContext } from 'react'
import { Link } from 'react-router-dom'
import { UserContext } from '../context/UserContext'

function Header() {
  const { user } = useContext(UserContext)

  return (
    <header className="bg-white shadow">
      <div className="container flex items-center justify-between h-16">
        <Link to="/" className="text-xl font-bold text-indigo-600">
          ShopSavy
        </Link>
        <nav className="flex items-center space-x-4">
          <Link to="/" className="text-gray-700 hover:text-indigo-600">
            Home
          </Link>
          {user ? (
            <div className="flex items-center space-x-2">
              <img 
                src="/src/assets/avatar.png" 
                alt="User Avatar" 
                className="w-8 h-8 rounded-full"
              />
              <span className="text-gray-700">{user.name}</span>
            </div>
          ) : (
            <button className="px-4 py-2 text-white bg-indigo-600 rounded hover:bg-indigo-700">
              Sign In
            </button>
          )}
        </nav>
      </div>
    </header>
  )
}

export default Header
