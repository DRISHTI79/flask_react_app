import { useEffect, useState } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import api from '../api'

export default function BlogForm() {
  const { id } = useParams()
  const isEdit = Boolean(id)
  const navigate = useNavigate()

  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(isEdit)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (isEdit) {
      api
        .get(`/blogs/${id}`)
        .then((res) => {
          setTitle(res.data.title)
          setContent(res.data.content)
        })
        .catch(() => setError('Could not load that post.'))
        .finally(() => setLoading(false))
    }
  }, [id, isEdit])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!title.trim() || !content.trim()) {
      setError('Title and content are required.')
      return
    }

    setSaving(true)
    try {
      if (isEdit) {
        await api.put(`/blogs/${id}`, { title, content })
        navigate(`/blogs/${id}`)
      } else {
        const res = await api.post('/blogs', { title, content })
        navigate(`/blogs/${res.data.id}`)
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Something went wrong.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="card card-wide">
        <p>Loading...</p>
      </div>
    )
  }

  return (
    <div className="card card-wide">
      {error && <div className="flash flash-error">{error}</div>}

      <h1>{isEdit ? 'Edit Post' : 'New Blog Post'}</h1>
      <form onSubmit={handleSubmit}>
        <label htmlFor="title">Title</label>
        <input
          id="title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />

        <label htmlFor="content">Content</label>
        <textarea
          id="content"
          rows={10}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          required
        />

        <button type="submit" disabled={saving}>
          {saving ? 'Saving...' : isEdit ? 'Save Changes' : 'Publish'}
        </button>
      </form>
      <p className="switch-link">
        <Link to="/blogs">&larr; Back to my blogs</Link>
      </p>
    </div>
  )
}
