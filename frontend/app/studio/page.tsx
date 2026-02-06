"use client"

import { useState, useEffect } from 'react'
import RequireAuth from '../../components/auth/RequireAuth'
import { useAuth } from '../../components/auth/AuthProvider'
import { config } from '../../lib/config'
import StudioInterface from '../../components/StudioInterface'

interface Project {
  id: number;
  name: string;
  description: string;
}

export default function StudioPage() {
  const { token, apiKey } = useAuth()
  const [loading, setLoading] = useState(true)
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<number | null>(null);

  useEffect(() => {
    if (!token) return;

    fetch(`${config.apiUrl}/api/v1/projects`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then((res) => res.json())
      .then((data) => {
        setProjects(data.projects || []);
        if (data.projects && data.projects.length > 0) {
          setSelectedProject(data.projects[0].id);
        }
        setLoading(false);
      })
      .catch((error) => {
        console.error('Failed to fetch projects:', error);
        setLoading(false);
      });
  }, [token]);

  if (loading) {
    return (
      <RequireAuth>
        <div className="w-screen h-screen bg-black flex items-center justify-center">
          <div className="text-center">
            <div className="w-12 h-12 rounded-full border-4 border-gray-700 border-t-purple-500 animate-spin mx-auto mb-4"></div>
            <p className="text-gray-400">Loading Studio...</p>
          </div>
        </div>
      </RequireAuth>
    )
  }

  return (
    <RequireAuth>
      <StudioInterface apiKey={apiKey || ''} />
    </RequireAuth>
  )
}
