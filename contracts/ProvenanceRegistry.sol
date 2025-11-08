// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

contract ProvenanceRegistry {
    event DisclosureRegistered(string tag, string hash, address contractAddr, uint256 blockNumber);

    function registerDisclosure(
        string calldata tag,
        string calldata hash,
        address contractAddr
    ) external {
        emit DisclosureRegistered(tag, hash, contractAddr, block.number);
    }
}
