import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import api from '../api'

export default function BlogView() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [blog, setBlog] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .get(`/blogs/${id}`)
      .then((res) => setBlog(res.data))
      .catch(() => setError('Blog post not found.'))
  }, [id])

  const handleDelete = async () => {
    if (!window.confirm('Delete this post?')) return
    try {
      await api.delete(`/blogs/${id}`)
      navigate('/blogs')
    } catch {
      setError('Could not delete that post.')
    }
  }

  if (error) {
    return (
      <div className="card card-wide">
        <div className="flash flash-error">{error}</div>
        <p className="switch-link">
          <Link to="/blogs">&larr; Back to my blogs</Link>
        </p>
      </div>
    )
  }

  if (!blog) {
    return (
      <div className="card card-wide">
        <p>Loading...</p>
      </div>
    )
  }

  const created = new Date(blog.created_at)
  const updated = new Date(blog.updated_at)
  const wasUpdated = blog.updated_at !== blog.created_at

  return (
    <div className="card card-wide">
      <h1>{blog.title}</h1>
      <p className="blog-meta">
        Posted {created.toLocaleDateString()}
        {wasUpdated ? ` · updated ${updated.toLocaleDateString()}` : ''}
      </p>
      <div className="blog-content">{blog.content}</div>

      <div className="blog-actions">
        <Link className="btn" to={`/blogs/${blog.id}/edit`}>
          Edit
        </Link>
        <button className="btn btn-danger" onClick={handleDelete}>
          Delete
        </button>
      </div>

      <p className="switch-link">
        <Link to="/blogs">&larr; Back to my blogs</Link>
      </p>
    </div>
  )
}
