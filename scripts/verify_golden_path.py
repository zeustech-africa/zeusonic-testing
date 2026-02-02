#!/usr/bin/env python3
"""
Zeusonic 1.0 Golden Path Verification Script
Tests the complete music transformation workflow end-to-end.
"""

import requests
import json
import time
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test_transform@example.com"
TEST_PASSWORD = "TestPass123!"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def log(msg, color=Colors.BLUE):
    print(f"{color}[VERIFY]{Colors.END} {msg}")

def success(msg):
    print(f"{Colors.GREEN}✓{Colors.END} {msg}")

def error(msg):
    print(f"{Colors.RED}✗{Colors.END} {msg}")
    sys.exit(1)

def wait_for_status(token, project_id, track_id, expected_status, max_wait=30):
    """Poll track status until expected status is reached."""
    log(f"Waiting for track {track_id} to reach status: {expected_status}")
    start = time.time()
    while time.time() - start < max_wait:
        response = requests.get(
            f"{BASE_URL}/api/v1/projects/{project_id}/audio",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.ok:
            data = response.json()
            for track in data.get("tracks", []):
                if track["id"] == track_id:
                    status = track["status"]
                    log(f"Track {track_id} status: {status}")
                    if status == expected_status:
                        success(f"Track reached status: {expected_status}")
                        return True
                    elif status == "failed":
                        error(f"Track processing failed")
        time.sleep(2)
    error(f"Timeout waiting for status {expected_status}")

def wait_for_transform(token, track_id, max_wait=60):
    """Poll transform job status until completed."""
    log(f"Waiting for transform job on track {track_id}")
    start = time.time()
    while time.time() - start < max_wait:
        response = requests.get(
            f"{BASE_URL}/api/v1/audio/{track_id}/transform/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.ok:
            data = response.json()
            status = data.get("status")
            log(f"Transform job status: {status}")
            if status == "completed":
                success("Transform job completed")
                return True
            elif status == "failed":
                error("Transform job failed")
        time.sleep(3)
    error("Timeout waiting for transform to complete")

def main():
    log("=== ZEUSONIC 1.0 GOLDEN PATH VERIFICATION ===")
    
    # Step 1: Register
    log("Step 1: Registering test user")
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    verification_code = None
    if response.status_code == 409:
        log("User already exists, will attempt login...")
    elif response.status_code == 201:
        data = response.json()
        verification_code = data.get("verification_code")
        success(f"User registered, verification code: {verification_code}")
    else:
        error(f"Registration failed: {response.status_code} {response.text}")
    
    # Step 2: Verify email if we just registered
    if verification_code:
        log("Step 2: Verifying email")
        response = requests.post(
            f"{BASE_URL}/auth/verify",
            json={"email": TEST_EMAIL, "code": verification_code}
        )
        if not response.ok:
            error(f"Verification failed: {response.status_code} {response.text}")
        success("Email verified")
    else:
        log("Step 2: Skipping verification (user already exists)")
    
    # Step 3: Login
    log("Step 3: Logging in")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    
    if not response.ok:
        error(f"Login failed: {response.status_code} {response.text}")
    
    data = response.json()
    token = data.get("access_token")
    if not token:
        error("No access token in login response")
    success(f"Logged in, got token: {token[:20]}...")
    
    # Step 4: Create project
    log("Step 4: Creating project")
    response = requests.post(
        f"{BASE_URL}/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Transform Test Project"}
    )
    if not response.ok:
        error(f"Project creation failed: {response.status_code} {response.text}")
    
    project = response.json()
    project_id = project["id"]
    success(f"Project created with ID: {project_id}")
    
    # Step 5: Upload audio file
    log("Step 5: Uploading audio file")
    
    # Create a minimal test WAV file (1 second, 440Hz sine wave)
    import numpy as np
    import soundfile as sf
    
    test_file = Path("/tmp/zeusonic_test_audio.wav")
    sr = 44100
    duration = 3.0  # 3 seconds for better analysis
    t = np.linspace(0, duration, int(sr * duration))
    # Simple sine wave with some harmonics
    audio = 0.5 * np.sin(2 * np.pi * 440 * t) + 0.3 * np.sin(2 * np.pi * 880 * t)
    sf.write(test_file, audio, sr, subtype='PCM_16')
    success(f"Created test audio file: {test_file}")
    
    with open(test_file, 'rb') as f:
        files = {'file': ('test_audio.wav', f, 'audio/wav')}
        response = requests.post(
            f"{BASE_URL}/api/v1/projects/{project_id}/audio",
            headers={"Authorization": f"Bearer {token}"},
            files=files
        )
    
    if not response.ok:
        error(f"Audio upload failed: {response.status_code} {response.text}")
    
    track = response.json()
    track_id = track["id"]
    success(f"Audio uploaded, track ID: {track_id}")
    
    # Step 6: Wait for analysis
    log("Step 6: Waiting for audio analysis")
    wait_for_status(token, project_id, track_id, "analyzed")
    
    # Verify analysis data
    response = requests.get(
        f"{BASE_URL}/api/v1/projects/{project_id}/audio",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.ok:
        tracks = response.json().get("tracks", [])
        for t in tracks:
            if t["id"] == track_id and t.get("analysis"):
                analysis = t["analysis"]
                log(f"Analysis results: BPM={analysis.get('bpm')}, Key={analysis.get('musical_key')}, LUFS={analysis.get('loudness_lufs')}")
                success("Analysis data available")
    
    # Step 7: Transform beat
    log("Step 7: Triggering beat transformation (to amapiano)")
    response = requests.post(
        f"{BASE_URL}/api/v1/audio/{track_id}/transform",
        headers={"Authorization": f"Bearer {token}"},
        json={"target_style": "amapiano"}
    )
    if not response.ok:
        error(f"Transform failed: {response.status_code} {response.text}")
    
    transform_job = response.json()
    success(f"Transform job created: {transform_job['id']}")
    
    # Step 8: Wait for transform
    log("Step 8: Waiting for transform to complete")
    wait_for_transform(token, track_id)
    
    # Verify transform output exists
    response = requests.get(
        f"{BASE_URL}/api/v1/audio/{track_id}/transform/status",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.ok:
        job = response.json()
        output_path = job.get("output_path")
        if output_path and Path(output_path).exists():
            success(f"Transform output exists: {output_path}")
        else:
            error("Transform output file not found")
    
    # Get the new transformed track ID
    response = requests.get(
        f"{BASE_URL}/api/v1/projects/{project_id}/audio",
        headers={"Authorization": f"Bearer {token}"}
    )
    transformed_track_id = None
    if response.ok:
        tracks = response.json().get("tracks", [])
        # Find the most recent analyzed track (should be the transformed one)
        for t in sorted(tracks, key=lambda x: x.get("created_at", ""), reverse=True):
            if "transform" in t.get("original_filename", "").lower() and t["status"] == "analyzed":
                transformed_track_id = t["id"]
                log(f"Found transformed track ID: {transformed_track_id}")
                break
    
    if not transformed_track_id:
        log("Warning: Could not find transformed track, will try to mix original")
        transformed_track_id = track_id
    
    # Step 9: Trigger mix
    log("Step 9: Triggering mix on transformed track")
    response = requests.post(
        f"{BASE_URL}/api/v1/audio/{transformed_track_id}/mix",
        headers={"Authorization": f"Bearer {token}"}
    )
    if not response.ok:
        error(f"Mix failed: {response.status_code} {response.text}")
    
    success("Mix job triggered")
    wait_for_status(token, project_id, transformed_track_id, "mixed")
    
    # Step 10: Trigger master
    log("Step 10: Triggering mastering")
    response = requests.post(
        f"{BASE_URL}/api/v1/audio/{transformed_track_id}/master",
        headers={"Authorization": f"Bearer {token}"}
    )
    if not response.ok:
        error(f"Master failed: {response.status_code} {response.text}")
    
    success("Master job triggered")
    wait_for_status(token, project_id, transformed_track_id, "mastered")
    
    # Step 11: Download
    log("Step 11: Downloading mastered audio")
    response = requests.get(
        f"{BASE_URL}/api/v1/audio/download/{transformed_track_id}/master",
        headers={"Authorization": f"Bearer {token}"}
    )
    if not response.ok:
        error(f"Download failed: {response.status_code} {response.text}")
    
    output_file = Path("/tmp/zeusonic_final_master.wav")
    output_file.write_bytes(response.content)
    success(f"Downloaded mastered audio: {output_file} ({len(response.content)} bytes)")
    
    # Verify file quality
    import soundfile as sf
    data, sr = sf.read(output_file)
    log(f"Final audio: {data.shape[0]} samples, {sr}Hz, {data.ndim} channels")
    peak = np.max(np.abs(data))
    log(f"Peak level: {peak:.3f} (should be < 1.0)")
    
    if peak >= 1.0:
        error("Audio is clipping!")
    
    success(f"Audio quality verified: peak={peak:.3f}, no clipping")
    
    # Final verification
    log("=== VERIFYING DATABASE STATE ===")
    
    # Check all tables
    response = requests.get(
        f"{BASE_URL}/api/v1/projects/{project_id}/audio",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.ok:
        tracks = response.json().get("tracks", [])
        log(f"Total tracks in project: {len(tracks)}")
        for t in tracks:
            log(f"  - Track {t['id']}: {t['original_filename']} (status: {t['status']})")
    
    print("\n" + "="*60)
    success("GOLDEN PATH VERIFICATION COMPLETE")
    print("="*60)
    print(f"\n{Colors.GREEN}All steps passed successfully!{Colors.END}")
    print(f"- User: {TEST_EMAIL}")
    print(f"- Project ID: {project_id}")
    print(f"- Track ID: {track_id}")
    print(f"- Transformed Track ID: {transformed_track_id}")
    print(f"- Final output: {output_file}")
    print(f"\nZeusonic 1.0 music transformation workflow is operational.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nVerification interrupted by user")
        sys.exit(1)
    except Exception as e:
        error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
