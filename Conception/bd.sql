-- User table
CREATE TABLE User (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    image VARCHAR(255),
    password VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at DATE DEFAULT CURRENT_DATE
);

-- Project table
CREATE TABLE Project (
    project_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    image VARCHAR(255),
    start_date DATE NULL,
    end_date DATE NULL,
    finished_date DATE NULL,
    created_at DATE DEFAULT CURRENT_DATE
);

-- Participate table (User-Project relationship)
CREATE TABLE Participate (
    user_id INT,
    project_id INT,
    role VARCHAR(50) NOT NULL,
    created_at DATE DEFAULT CURRENT_DATE,
    PRIMARY KEY (user_id, project_id),
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES Project(project_id) ON DELETE CASCADE
);

-- Task table
CREATE TABLE Task (
    task_id INT PRIMARY KEY AUTO_INCREMENT,
    project_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    priority VARCHAR(10) CHECK (priority IN ('low', 'medium', 'high')),
    status ENUM('TODO', 'IN_PROGRESS', 'REVIEW', 'DONE') DEFAULT 'TODO',
    start_date DATE NULL,
    end_date DATE NULL,
    finished_date DATE NULL,
    created_at DATE DEFAULT CURRENT_DATE,
    FOREIGN KEY (project_id) REFERENCES Project(project_id) ON DELETE CASCADE
);

-- Task Predecessor relationship
CREATE TABLE Predecessor (
    task_id INT,
    predecessor_id INT,
    created_at DATE DEFAULT CURRENT_DATE,
    PRIMARY KEY (task_id, predecessor_id),
    FOREIGN KEY (task_id) REFERENCES Task(task_id) ON DELETE CASCADE,
    FOREIGN KEY (predecessor_id) REFERENCES Task(task_id) ON DELETE CASCADE,
    CHECK (task_id != predecessor_id)
);

-- Task Assignment with Notes
CREATE TABLE Assigned (
    user_id INT,
    task_id INT,
    note TEXT,
    created_at DATE DEFAULT CURRENT_DATE,
    PRIMARY KEY (user_id, task_id),
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES Task(task_id) ON DELETE CASCADE
);

-- Add indexes for better performance
CREATE INDEX idx_task_project ON Task(project_id);
CREATE INDEX idx_task_status ON Task(status);
CREATE INDEX idx_participate_project ON Participate(project_id);
CREATE INDEX idx_participate_user ON Participate(user_id);
CREATE INDEX idx_assigned_task ON Assigned(task_id);
CREATE INDEX idx_assigned_user ON Assigned(user_id);

-- Add some sample data
INSERT INTO articipate (user_id, project_id, role) VALUES (2, 1, 'membre');