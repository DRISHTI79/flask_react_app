import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import api from '../api'

export default function Dashboard() {
  const { user, logout } = useAuth()
  const [blogCount, setBlogCount] = useState(0)

  useEffect(() => {
    api
      .get('/blogs')
      .then((res) => setBlogCount(res.data.length))
      .catch(() => setBlogCount(0))
  }, [])

  return (
    <div className="card">
      <h1>Welcome, {user?.username}!</h1>
      <p>You're logged in. This is your dashboard.</p>
      <p>
        You have <strong>{blogCount}</strong> blog post{blogCount !== 1 ? 's' : ''}.
      </p>

      <Link className="btn" to="/blogs">
        Manage My Blogs
      </Link>
      <button className="btn btn-secondary" onClick={logout}>
        Log out
      </button>
    </div>
  )
}
