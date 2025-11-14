use borsh::{BorshDeserialize, BorshSerialize};
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint, entrypoint::ProgramResult,
    msg,
    program::{invoke_signed},
    program_error::ProgramError,
    pubkey::Pubkey,
};

#[derive(BorshDeserialize, BorshSerialize, Debug)]
pub struct SwapLeg {
    pub pool_program: Pubkey,
    pub pool_account: Pubkey,
    pub token_in: Pubkey,
    pub token_out: Pubkey,
    pub amount_in: u64,
    pub min_out: u64,
}

#[derive(BorshDeserialize, BorshSerialize, Debug)]
pub struct SwapBundle {
    pub legs: Vec<SwapLeg>,
}

entrypoint!(process_instruction);

pub fn process_instruction(
    _program_id: &Pubkey,
    accounts: &[AccountInfo],
    data: &[u8],
) -> ProgramResult {
    let bundle = SwapBundle::try_from_slice(data).map_err(|_| ProgramError::InvalidInstructionData)?;
    let accounts_iter = &mut accounts.iter();

    let _user = next_account_info(accounts_iter)?;
    let _vault = next_account_info(accounts_iter)?;

    msg!("router::bundle_start legs={}", bundle.legs.len());

    // On-chain validation of the swap path
    validate_swap_path(&bundle.legs)?;

    for (i, leg) in bundle.legs.iter().enumerate() {
        msg!("leg {} program={}", i, leg.pool_program);
        if !is_whitelisted(&leg.pool_program) {
            msg!("non-whitelisted pool {}", leg.pool_program);
            return Err(ProgramError::Custom(99));
        }

        // Safety: check expected accounts exist in the slice
        let pool_acc = next_account_info(accounts_iter)?;
        let token_in_acc = next_account_info(accounts_iter)?;
        let token_out_acc = next_account_info(accounts_iter)?;

        let ix = solana_program::instruction::Instruction {
            program_id: leg.pool_program,
            accounts: vec![
                solana_program::instruction::AccountMeta::new(*token_in_acc.key, false),
                solana_program::instruction::AccountMeta::new(*token_out_acc.key, false),
                solana_program::instruction::AccountMeta::new(*pool_acc.key, false),
            ],
            data: vec![], // actual AMM program data built off-chain
        };

        invoke_signed(
            &ix,
            &[pool_acc.clone(), token_in_acc.clone(), token_out_acc.clone()],
            &[],
        )?;
    }

    msg!("router::bundle_complete");
    Ok(())
}

fn validate_swap_path(legs: &[SwapLeg]) -> ProgramResult {
    if legs.is_empty() {
        msg!("Swap path cannot be empty");
        return Err(ProgramError::InvalidInstructionData);
    }

    for i in 0..legs.len() - 1 {
        let current_leg = &legs[i];
        let next_leg = &legs[i + 1];

        if current_leg.token_out != next_leg.token_in {
            msg!(
                "Invalid swap path: token mismatch between leg {} and {}",
                i,
                i + 1
            );
            return Err(ProgramError::InvalidInstructionData);
        }
    }

    Ok(())
}

fn is_whitelisted(pid: &Pubkey) -> bool {
    const RAYDIUM_V4: &str = "675kPX9MHTjS2EMi9PgcJRCQXDboY1wG2Lr1AsF2Vjc";
    const ORCA_WHIRLPOOL: &str = "whirLbXNDv1Xz2ZRLZCuV8QnbWaoK1J7tqUfFzQ6U9a";
    const METEORA_DLMM: &str = "DLMMoo11yxxxxx8zkxaq5J8rP4F92VkxAv9xfrVvZLL";
    let ok = [RAYDIUM_V4, ORCA_WHIRLPOOL, METEORA_DLMM]
        .iter()
        .any(|x| *pid == x.parse().unwrap());
    ok
}
