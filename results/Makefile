clean-all:
	rm -rf */*/*/spectators
	rm -rf */*/*/session
	rm -rf */*.dat
	
clean-data:
	rm -rf */*/*/*/data
	rm -rf */*/*/*/*/data
	rm -rf */*.dat

clean-diagrams:
	rm -rf */*/*/*/diagrams
	rm -rf */*/*/*/*/diagrams

spectator-data:
	python3 make_spectator_data.py

spectator-diagrams:
	python3 make_spectator_diagrams.py

spectator-all:
	python3 make_spectator_data.py
	python3 make_spectator_diagrams.py

session-data:
	python3 make_session_data.py

session-diagrams:
	python3 make_session_diagrams.py

session-all:
	python3 make_session_data.py
	python3 make_session_diagrams.py

all-data:
	python3 make_spectator_data.py
	python3 make_session_data.py
	./create_combined_data.sh

all-diagrams:
	python3 make_spectator_diagrams.py
	python3 make_session_diagrams.py

all:
	python3 make_spectator_data.py
	python3 make_session_data.py
	./create_combined_data.sh
	python3 make_spectator_diagrams.py
	python3 make_session_diagrams.py
	python3 make_session_combined_diagrams.py
