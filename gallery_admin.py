"""Public gallery and admin photo management using the existing login and database."""
import json
import secrets

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, Response

from employee_admin import check_csrf, database, read_photo, redirect, render, session

router = APIRouter()


def gallery_photos():
    with database() as db:
        return db.execute('SELECT id, description, photo_version FROM gallery_photos ORDER BY sort_order, id').fetchall()


def get_photo(photo_id):
    with database() as db:
        row = db.execute('SELECT id, description, photo_version FROM gallery_photos WHERE id = ?', (photo_id,)).fetchone()
    if row is None:
        raise HTTPException(404, 'Photo not found')
    return row


def gallery_dashboard(request, current, error=None, notice=None):
    return render(request, 'admin_gallery.html', photos=gallery_photos(), csrf=current['csrf'], error=error, notice=notice)


@router.get('/gallery', response_class=HTMLResponse)
async def public_gallery(request: Request):
    return render(request, 'gallery.html', photos=gallery_photos())


@router.get('/gallery/photos/{photo_id:int}')
async def gallery_image(photo_id: int):
    with database() as db:
        row = db.execute('SELECT photo FROM gallery_photos WHERE id = ?', (photo_id,)).fetchone()
    if row is None:
        raise HTTPException(404, 'Photo not found')
    return Response(bytes(row['photo']), media_type='image/jpeg', headers={'Cache-Control': 'no-cache', 'X-Content-Type-Options': 'nosniff'})


@router.get('/admin/gallery', response_class=HTMLResponse)
async def admin_gallery(request: Request):
    current = session(request)
    if not current or not current['authenticated']:
        return redirect('/admin/login')
    notices = {'saved': 'Photo saved. The gallery is up to date.', 'deleted': 'Photo removed.', 'arranged': 'Gallery order saved.'}
    return gallery_dashboard(request, current, notice=notices.get(request.query_params.get('notice')))


@router.get('/admin/gallery/new', response_class=HTMLResponse)
@router.get('/admin/gallery/{photo_id:int}/edit', response_class=HTMLResponse)
async def gallery_form(request: Request, photo_id: int = None):
    current = session(request)
    if not current or not current['authenticated']:
        return redirect('/admin/login')
    photo = get_photo(photo_id) if photo_id else {'description': ''}
    return render(request, 'admin_gallery_form.html', photo=photo, csrf=current['csrf'])


@router.post('/admin/gallery/new')
@router.post('/admin/gallery/{photo_id:int}/edit')
async def save_gallery_photo(request: Request, photo_id: int = None, csrf: str = Form(''), description: str = Form(''), photo: UploadFile = File(None)):
    current = check_csrf(request, csrf)
    existing = get_photo(photo_id) if photo_id else None
    values = {'id': photo_id, 'description': description.strip(), 'photo_version': existing['photo_version'] if existing else None}
    try:
        if len(values['description']) > 200:
            raise ValueError('Keep the photo description to 200 characters or fewer.')
        image = await read_photo(photo)
        if not existing and image is None:
            raise ValueError('Choose a photo to add to the gallery.')
    except ValueError as exc:
        response = render(request, 'admin_gallery_form.html', photo=values, csrf=current['csrf'], error=str(exc))
        response.status_code = 400
        return response
    with database() as db:
        if existing:
            db.execute('UPDATE gallery_photos SET description = ? WHERE id = ?', (values['description'], photo_id))
            if image is not None:
                db.execute('UPDATE gallery_photos SET photo = ?, photo_version = ? WHERE id = ?', (image, secrets.token_hex(8), photo_id))
        else:
            db.execute('BEGIN IMMEDIATE')
            order = db.execute('SELECT COALESCE(MAX(sort_order), -1) + 1 FROM gallery_photos').fetchone()[0]
            db.execute('INSERT INTO gallery_photos (description, photo, photo_version, sort_order) VALUES (?, ?, ?, ?)', (values['description'], image, secrets.token_hex(8), order))
    return redirect('/admin/gallery?notice=saved')


@router.post('/admin/gallery/{photo_id:int}/delete')
async def delete_gallery_photo(request: Request, photo_id: int, csrf: str = Form('')):
    check_csrf(request, csrf)
    get_photo(photo_id)
    with database() as db:
        db.execute('DELETE FROM gallery_photos WHERE id = ?', (photo_id,))
    return redirect('/admin/gallery?notice=deleted')


@router.post('/admin/gallery/{photo_id:int}/move')
async def move_gallery_photo(request: Request, photo_id: int, csrf: str = Form(''), direction: str = Form('')):
    check_csrf(request, csrf)
    if direction not in {'earlier', 'later'}:
        raise HTTPException(400, 'Choose earlier or later.')
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        ids = [row[0] for row in db.execute('SELECT id FROM gallery_photos ORDER BY sort_order, id')]
        if photo_id not in ids:
            raise HTTPException(404, 'Photo not found')
        position = ids.index(photo_id)
        target = position + (-1 if direction == 'earlier' else 1)
        if 0 <= target < len(ids):
            ids[position], ids[target] = ids[target], ids[position]
            db.executemany('UPDATE gallery_photos SET sort_order = ? WHERE id = ?', enumerate(ids))
    return redirect('/admin/gallery?notice=arranged')


@router.post('/admin/gallery/reorder')
async def reorder_gallery(request: Request, csrf: str = Form(''), order: str = Form('')):
    current = check_csrf(request, csrf)
    try:
        ids = json.loads(order)
        if not isinstance(ids, list) or any(type(value) is not int for value in ids):
            raise ValueError()
    except (ValueError, TypeError):
        raise HTTPException(400, 'Invalid gallery order.')
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        current_ids = [row[0] for row in db.execute('SELECT id FROM gallery_photos')]
        changed = sorted(ids) != sorted(current_ids)
        if not changed:
            db.executemany('UPDATE gallery_photos SET sort_order = ? WHERE id = ?', enumerate(ids))
    if changed:
        response = gallery_dashboard(request, current, error='The gallery changed in another window. Please arrange the current photos again.')
        response.status_code = 409
        return response
    return redirect('/admin/gallery?notice=arranged')
