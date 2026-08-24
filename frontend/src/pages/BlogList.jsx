import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api'

export default function BlogList() {
  const [blogs, setBlogs] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const loadBlogs = () => {
    setLoading(true)
    api
      .get('/blogs')
      .then((res) => setBlogs(res.data))
      .catch(() => setError('Could not load your blogs.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadBlogs()
  }, [])

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this post?')) return
    try {
      await api.delete(`/blogs/${id}`)
      setBlogs(blogs.filter((b) => b.id !== id))
    } catch {
      setError('Could not delete that post.')
    }
  }

  return (
    <div className="card card-wide">
      {error && <div className="flash flash-error">{error}</div>}

      <div className="blog-header">
        <h1>My Blogs</h1>
        <Link className="btn" to="/blogs/new">
          + New Post
        </Link>
      </div>

      {loading ? (
        <p>Loading...</p>
      ) : blogs.length > 0 ? (
        <ul className="blog-list">
          {blogs.map((blog) => (
            <li className="blog-item" key={blog.id}>
              <Link className="blog-title" to={`/blogs/${blog.id}`}>
                {blog.title}
              </Link>
              <p className="blog-snippet">
                {blog.content.slice(0, 120)}
                {blog.content.length > 120 ? '...' : ''}
              </p>
              <div className="blog-meta">
                <span>{new Date(blog.created_at).toLocaleDateString()}</span>
                <Link to={`/blogs/${blog.id}/edit`}>Edit</Link>
                <button className="link-btn" onClick={() => handleDelete(blog.id)}>
                  Delete
                </button>
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p>You haven't written any blog posts yet.</p>
      )}

      <p className="switch-link">
        <Link to="/dashboard">&larr; Back to dashboard</Link>
      </p>
    </div>
  )
}
