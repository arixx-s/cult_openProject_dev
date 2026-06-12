INSERT INTO users (name, email, password_hash, role) VALUES
('Admin User', 'admin@example.com', '8f7cf196421c68b86dff81b2dadf5af7$cdbfdcc80545fd8ba97b620f3519f139a8745581f31919895e20ad66d40ead16', 'admin'),
('Riya Sharma', 'riya@example.com', '8f7cf196421c68b86dff81b2dadf5af7$cdbfdcc80545fd8ba97b620f3519f139a8745581f31919895e20ad66d40ead16', 'user');

INSERT INTO assets (asset_name, category, description, quantity_total, status) VALUES
('Canon EOS 90D DSLR', 'Camera', 'DSLR camera with 18-135mm kit lens for event coverage.', 4, 'Available'),
('Sony A7 III Mirrorless Camera', 'Camera', 'Full-frame camera used for low-light concerts and interviews.', 2, 'Available'),
('Godox SL-60W Studio Light', 'Lighting', 'Continuous studio light with stand and softbox.', 6, 'Available'),
('Shure SM58 Microphone', 'Audio', 'Wired vocal microphone for stage and recording use.', 10, 'Available'),
('Yamaha MG10XU Audio Mixer', 'Audio', 'Compact mixer with USB interface for small events.', 3, 'Available'),
('Traditional Costume Set', 'Costume', 'Curated costume set for cultural performances.', 12, 'Available'),
('Wooden Stage Prop Kit', 'Stage Props', 'Reusable props for stage backdrops and skits.', 5, 'Available'),
('Portable Recording Kit', 'Recording', 'Audio recorder, tripod, headphones and memory card kit.', 3, 'Available'),
('Foldable Event Barricade', 'Event Infrastructure', 'Lightweight barricades for venue flow control.', 20, 'Available');

INSERT INTO bookings (asset_id, user_id, quantity_requested, start_date, end_date, purpose, status) VALUES
(1, 2, 1, date('now', '+1 day'), date('now', '+3 day'), 'Photography for music night.', 'pending'),
(4, 2, 3, date('now'), date('now', '+2 day'), 'Open mic rehearsal setup.', 'approved'),
(3, 2, 2, date('now', '-6 day'), date('now', '-2 day'), 'Interview lighting for teaser shoot.', 'returned');
