"use client"

import { useState, useEffect } from 'react'
import AppLayout from '../../components/AppLayout'
import AudioProcessor from '../../components/AudioProcessor'
import RequireAuth from '../../components/auth/RequireAuth'
import { useAuth } from '../../components/auth/AuthProvider'
import { config } from '../../lib/config'

interface Project {
  id: number;
  name: string;
  description: string;
}

export default function StudioPage() {
  const { token } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

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
        <AppLayout title="Audio Studio">
          <div className="p-6">
            <p className="text-gray-400">Loading...</p>
          </div>
        </AppLayout>
      </RequireAuth>
    );
  }

  if (projects.length === 0) {
    return (
      <RequireAuth>
        <AppLayout title="Audio Studio">
          <div className="p-6">
            <div className="p-6 bg-black/30 rounded-lg border border-purple-500/20 text-center">
              <h2 className="text-xl font-bold text-white mb-2">No Projects Yet</h2>
              <p className="text-gray-400 mb-4">Create a project first to upload and process audio.</p>
              <a
                href="/dashboard"
                className="inline-block px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:opacity-90 transition-opacity"
              >
                Go to Dashboard
              </a>
            </div>
          </div>
        </AppLayout>
      </RequireAuth>
    );
  }

  return (
    <RequireAuth>
      <AppLayout title="Audio Studio">
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold text-white">Audio Studio</h1>
            
            {/* Project Selector */}
            {projects.length > 1 && (
              <select
                value={selectedProject || ''}
                onChange={(e) => setSelectedProject(Number(e.target.value))}
                className="px-4 py-2 bg-black/50 border border-purple-500/30 rounded-lg text-white"
              >
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            )}
          </div>

          <p className="text-gray-400">
            Upload audio files, analyze them, and apply AI-powered mixing and mastering.
          </p>

          {selectedProject && <AudioProcessor projectId={selectedProject} />}
        </div>
      </AppLayout>
    </RequireAuth>
  );
}
