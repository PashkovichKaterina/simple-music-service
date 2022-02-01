import React from 'react';
import '../style/SongPlayer.css'

class SongPlayerContainer extends React.PureComponent {
    constructor(props) {
        super(props);
        this.state = {
            song: {}
        }
    }

    componentDidMount() {
        fetch("songs/1")
            .then(response => response.json())
            .then(json => this.setState({song: json}))
    }

    render() {
        const {title, artist, location} = this.state.song
        return (
            <div className="song-player">
                <p className="title">{title}</p>
                <p className="artist">{artist}</p>
                <audio src={location}
                       controls={true}
                       className="player-component"/>
            </div>
        )
    }
}

export default SongPlayerContainer;
