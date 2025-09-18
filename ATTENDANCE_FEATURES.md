# New Attendance Features

## Overview
The Engage Portal System has been enhanced with improved attendance management and parent notification features.

## New Features

### 1. Enhanced Attendance Marking
- **Three Attendance Buttons**: Present, Absent, and Late
- **Visual Status Display**: Color-coded attendance status
  - Green: Present
  - Red: Absent  
  - Yellow: Late
  - Gray: Not marked
- **Real-time Updates**: Attendance status updates immediately when marked

### 2. Parent Email Notifications
- **Email Parents Button**: Send notifications directly to parents
- **Gmail SMTP Integration**: Uses Gmail's SMTP server for reliable email delivery
- **Pre-made Messages**: Automatically generates appropriate messages based on attendance status
- **Customizable Content**: Teachers can modify subject and message content

## How to Use

### For Teachers/Admins:

#### Marking Attendance:
1. Navigate to classroom details
2. In the Students section, use the three buttons:
   - **Present**: Student is in class
   - **Absent**: Student is not in class
   - **Late**: Student arrived late

#### Sending Parent Notifications:
1. After marking a student as Absent or Late, click **"Email Parents"**
2. Enter your email credentials:
   - **Your Email**: Your Gmail address
   - **Password**: Your Gmail App Password (not regular password)
3. Review and modify the subject and message if needed
4. Click **"Send Email"**

### Gmail App Password Setup:
1. Go to your Google Account settings
2. Navigate to Security > App passwords
3. Generate a new app password for "Mail"
4. Use this app password (not your regular Gmail password)

## Technical Details

### Database Changes:
- Updated `Attendance` model to support 'late' status
- Existing 'present' and 'absent' statuses remain unchanged

### Email Configuration:
- Uses Gmail SMTP server (smtp.gmail.com:587)
- Supports TLS encryption
- Handles authentication errors gracefully

### Both Versions Updated:
- **Web Application**: Enhanced HTML interface with styled buttons
- **Desktop Application**: Updated PyQt5 interface with improved functionality

## File Changes:
- `database.py`: Updated attendance status support
- `app.py`: Added email routes and enhanced attendance marking
- `desktop_app.py`: Added Late button and improved email functionality
- `templates/classroom_details.html`: New button interface
- `templates/send_notification.html`: New email form
- `static/style.css`: Styling for new buttons and forms

## Security Notes:
- Email credentials are not stored permanently
- App passwords are recommended for Gmail accounts
- All email operations are logged for audit purposes

